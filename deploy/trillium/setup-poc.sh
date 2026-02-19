#!/bin/bash
#
# HealthDataNexus PoC Setup Script for Trillium
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load config
if [ -f "${SCRIPT_DIR}/.env" ]; then
    set -a; source "${SCRIPT_DIR}/.env"; set +a
elif [ -f "${SCRIPT_DIR}/.env.example" ]; then
    echo "Warning: using .env.example"; set -a; source "${SCRIPT_DIR}/.env.example"; set +a
else
    echo "Error: No .env found"; exit 1
fi

setup_directories() {
    echo "=== Setting up directories ==="
    mkdir -p "${POC_DIR}/data/postgres" "${POC_DIR}/data/postgres-socket" \
             "${POC_DIR}/data/media"/{active-projects,archived-projects,credential-applications,published-projects,users} \
             "${POC_DIR}/data/static/published-projects" \
             "${POC_DIR}/logs" "${POC_DIR}/containers" \
             "${SCRATCH_DIR}/apptainer_cache" "${SCRATCH_DIR}/tmp" 2>/dev/null || true
    echo "Done"
}

pull_containers() {
    echo "=== Pulling containers ==="
    export APPTAINER_CACHEDIR="${SCRATCH_DIR}/apptainer_cache"
    export TMPDIR="${SCRATCH_DIR}/tmp"
    cd "${POC_DIR}/containers"

    [ ! -f postgres.sif ] && apptainer pull docker://postgres:13-alpine && mv postgres*.sif postgres.sif 2>/dev/null || true
    [ ! -f health-data-nexus.sif ] && apptainer pull "${APP_IMAGE}" && mv health-data-nexus*.sif health-data-nexus.sif 2>/dev/null || true

    echo "Containers:"; ls -lh "${POC_DIR}/containers/"
}

start_postgres() {
    echo "=== Starting PostgreSQL ==="
    if [ -f "${POC_DIR}/postgres.pid" ] && kill -0 "$(cat ${POC_DIR}/postgres.pid)" 2>/dev/null; then
        echo "Already running"; return 0
    fi
    rm -f "${POC_DIR}/postgres.pid"

    if [ ! -f "${POC_DIR}/data/postgres/PG_VERSION" ]; then
        echo "Initializing..."
        apptainer exec --bind "${POC_DIR}/data/postgres:/var/lib/postgresql/data" \
            "${POC_DIR}/containers/postgres.sif" initdb -U "${DB_USER}" -D /var/lib/postgresql/data
        cat >> "${POC_DIR}/data/postgres/postgresql.conf" << 'EOF'
listen_addresses = '*'
unix_socket_directories = '/var/run/postgresql'
EOF
        echo "host all all 0.0.0.0/0 trust" >> "${POC_DIR}/data/postgres/pg_hba.conf"
        echo "local all all trust" >> "${POC_DIR}/data/postgres/pg_hba.conf"
    fi

    apptainer exec --bind "${POC_DIR}/data/postgres:/var/lib/postgresql/data" \
        --bind "${POC_DIR}/data/postgres-socket:/var/run/postgresql" \
        "${POC_DIR}/containers/postgres.sif" \
        postgres -D /var/lib/postgresql/data -p "${DB_PORT}" > "${POC_DIR}/logs/postgres.log" 2>&1 &
    echo $! > "${POC_DIR}/postgres.pid"

    for i in {1..30}; do [ -S "${POC_DIR}/data/postgres-socket/.s.PGSQL.${DB_PORT}" ] && break; sleep 1; done

    apptainer exec --bind "${POC_DIR}/data/postgres-socket:/var/run/postgresql" \
        "${POC_DIR}/containers/postgres.sif" \
        createdb -U "${DB_USER}" -h /var/run/postgresql -p "${DB_PORT}" "${DB_NAME}" 2>/dev/null || true
    echo "PostgreSQL ready (PID: $(cat ${POC_DIR}/postgres.pid))"
}

run_collectstatic() {
    echo "=== Collecting static files ==="
    apptainer exec --writable-tmpfs --pwd /code \
        --bind "${POC_DIR}/data/static:${STATIC_ROOT}" \
        --bind "${POC_DIR}/data/postgres-socket:/var/run/postgresql" \
        --env SECRET_KEY="${SECRET_KEY}" --env DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE}" \
        --env DB_HOST="/var/run/postgresql" --env DB_PORT="${DB_PORT}" \
        --env DB_NAME="${DB_NAME}" --env DB_USER="${DB_USER}" --env DB_PASSWORD="${DB_PASSWORD}" \
        --env STATIC_ROOT="${STATIC_ROOT}" --env STORAGE_TYPE="${STORAGE_TYPE}" \
        --env GCP_STATIC_BUCKET_NAME="${GCP_STATIC_BUCKET_NAME}" \
        --env SITE_NAME="${SITE_NAME}" --env STRAPLINE="${STRAPLINE}" \
        --env EMAIL_SIGNATURE="${EMAIL_SIGNATURE}" --env FOOTER_MANAGED_BY="${FOOTER_MANAGED_BY}" \
        --env FOOTER_SUPPORTED_BY="${FOOTER_SUPPORTED_BY}" \
        "${POC_DIR}/containers/health-data-nexus.sif" \
        python physionet-django/manage.py collectstatic --noinput
}

start_worker_bg() {
    echo "=== Starting Django Q2 worker (background) ==="
    if [ -f "${POC_DIR}/worker.pid" ] && kill -0 "$(cat ${POC_DIR}/worker.pid)" 2>/dev/null; then
        echo "Worker already running"; return 0
    fi
    rm -f "${POC_DIR}/worker.pid"

    nohup apptainer exec --writable-tmpfs --pwd /code \
        --bind "${POC_DIR}/data/postgres-socket:/var/run/postgresql" \
        --env SECRET_KEY="${SECRET_KEY}" --env DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE}" \
        --env DB_HOST="/var/run/postgresql" --env DB_PORT="${DB_PORT}" \
        --env DB_NAME="${DB_NAME}" --env DB_USER="${DB_USER}" --env DB_PASSWORD="${DB_PASSWORD}" \
        --env STORAGE_TYPE="${STORAGE_TYPE}" --env GCP_MEDIA_BUCKET_NAME="${GCP_MEDIA_BUCKET_NAME}" \
        --env SITE_NAME="${SITE_NAME}" --env STRAPLINE="${STRAPLINE}" \
        --env EMAIL_SIGNATURE="${EMAIL_SIGNATURE}" --env FOOTER_MANAGED_BY="${FOOTER_MANAGED_BY}" \
        --env FOOTER_SUPPORTED_BY="${FOOTER_SUPPORTED_BY}" \
        "${POC_DIR}/containers/health-data-nexus.sif" \
        python physionet-django/manage.py qcluster > "${POC_DIR}/logs/worker.log" 2>&1 &
    echo $! > "${POC_DIR}/worker.pid"
    echo "Worker started (PID: $(cat ${POC_DIR}/worker.pid))"
}

start_app_bg() {
    echo "=== Starting Application (background) ==="
    if [ -f "${POC_DIR}/app.pid" ] && kill -0 "$(cat ${POC_DIR}/app.pid)" 2>/dev/null; then
        echo "App already running"; return 0
    fi
    rm -f "${POC_DIR}/app.pid"

    nohup apptainer exec --writable-tmpfs --pwd /code \
        --bind "${POC_DIR}/data/media:${MEDIA_ROOT}" --bind "${POC_DIR}/data/static:${STATIC_ROOT}" \
        --bind "${POC_DIR}/data/postgres-socket:/var/run/postgresql" \
        --env SECRET_KEY="${SECRET_KEY}" --env DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE}" \
        --env DEBUG="${DEBUG}" --env ALLOWED_HOSTS="${ALLOWED_HOSTS}" --env SITE_ID="${SITE_ID}" \
        --env DB_HOST="/var/run/postgresql" --env DB_PORT="${DB_PORT}" --env DB_NAME="${DB_NAME}" \
        --env DB_USER="${DB_USER}" --env DB_PASSWORD="${DB_PASSWORD}" --env STORAGE_TYPE="${STORAGE_TYPE}" \
        --env MEDIA_ROOT="${MEDIA_ROOT}" --env STATIC_ROOT="${STATIC_ROOT}" \
        --env GCP_MEDIA_BUCKET_NAME="${GCP_MEDIA_BUCKET_NAME}" --env GCP_STATIC_BUCKET_NAME="${GCP_STATIC_BUCKET_NAME}" \
        --env SITE_NAME="${SITE_NAME}" --env STRAPLINE="${STRAPLINE}" --env EMAIL_SIGNATURE="${EMAIL_SIGNATURE}" \
        --env FOOTER_MANAGED_BY="${FOOTER_MANAGED_BY}" --env FOOTER_SUPPORTED_BY="${FOOTER_SUPPORTED_BY}" \
        "${POC_DIR}/containers/health-data-nexus.sif" \
        bash -c "python physionet-django/manage.py migrate && python physionet-django/manage.py runserver 0.0.0.0:${APP_PORT}" \
        > "${POC_DIR}/logs/app.log" 2>&1 &
    echo $! > "${POC_DIR}/app.pid"
    echo "App started (PID: $(cat ${POC_DIR}/app.pid))"
}

stop_services() {
    echo "=== Stopping services ==="
    for pid_file in app.pid worker.pid postgres.pid; do
        [ -f "${POC_DIR}/${pid_file}" ] && kill "$(cat ${POC_DIR}/${pid_file})" 2>/dev/null || true
        rm -f "${POC_DIR}/${pid_file}"
    done
    pkill -f "postgres.*${DB_PORT}" 2>/dev/null || true
    pkill -f "manage.py runserver.*${APP_PORT}" 2>/dev/null || true
    pkill -f "manage.py qcluster" 2>/dev/null || true
    echo "Stopped"
}

status() {
    echo "=== Status ==="
    for service in postgres app worker; do
        if [ -f "${POC_DIR}/${service}.pid" ] && kill -0 "$(cat ${POC_DIR}/${service}.pid)" 2>/dev/null; then
            echo "${service}: Running (PID: $(cat ${POC_DIR}/${service}.pid))"
        else
            echo "${service}: Stopped"
        fi
    done
}

show_logs() { [ -f "${POC_DIR}/logs/app.log" ] && tail -f "${POC_DIR}/logs/app.log" || echo "No app logs"; }
show_logs_worker() { [ -f "${POC_DIR}/logs/worker.log" ] && tail -f "${POC_DIR}/logs/worker.log" || echo "No worker logs"; }
show_logs_db() { [ -f "${POC_DIR}/logs/postgres.log" ] && tail -f "${POC_DIR}/logs/postgres.log" || echo "No db logs"; }

case "${1:-}" in
    setup) setup_directories ;;
    pull) pull_containers ;;
    collectstatic) run_collectstatic ;;
    start-db) start_postgres ;;
    start-worker) start_worker_bg ;;
    start-bg) setup_directories; pull_containers; start_postgres; run_collectstatic; start_worker_bg; start_app_bg ;;
    stop) stop_services ;;
    status) status ;;
    logs) show_logs ;;
    logs-worker) show_logs_worker ;;
    logs-db) show_logs_db ;;
    *) echo "Usage: $0 {setup|pull|collectstatic|start-db|start-worker|start-bg|stop|status|logs|logs-worker|logs-db}"; exit 1 ;;
esac
