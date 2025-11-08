module.exports = {
  apps: [{
    name: 'dflow-txns-alert',
    script: 'Dflow_Transactions.py',
    interpreter: 'python3',
    cwd: '/root/dflow-txns-alert',
    autorestart: false,
    watch: false,
    cron_restart: '*/5 * * * *',  // Run every 5 minutes
    error_file: '/root/dflow-txns-alert/logs/error.log',
    out_file: '/root/dflow-txns-alert/logs/out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true
  }]
};

