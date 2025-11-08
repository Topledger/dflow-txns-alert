module.exports = {
  apps: [{
    name: 'dflow-txns-alert',
    script: '/usr/bin/python3',
    args: '/root/dflow-txns-alert/Dflow_Transactions.py',
    cwd: '/root/dflow-txns-alert',
    interpreter: 'none',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production',
      TG_BOT_TOKEN: 'bot8443866055:AAHwfJYhU9rAkNo_sIhfD46x7sFvi4WhJrE',
      TG_CHAT_ID: '-1003269167073',
      TIMEOUT_SEC: '5',
      EXPECT_STATUS: '200',
      MAX_LATENCY_MS: '1500',
      HEARTBEAT_MIN: '0'
    },
    error_file: '/root/dflow-txns-alert/logs/error.log',
    out_file: '/root/dflow-txns-alert/logs/out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    cron_restart: '*/5 * * * *',  // Restart every 5 minutes to run the check
    autorestart: false  // Don't auto-restart since it's a cron job
  }]
};

