module.exports = {
    apps: [
        {
            name: 'myapp-frontend',
            script: 'node_modules/.bin/next',
            args: 'start',
            cwd: '/home/odya/gtk_new/frontend',
            instances: 1,          // или 'max' для cluster mode
            exec_mode: 'fork',
            env: {
                NODE_ENV: 'production',
                PORT: 3000,
            },
            error_file: '/var/log/pm2/myapp-frontend-err.log',
            out_file: '/var/log/pm2/myapp-frontend-out.log',
            log_date_format: 'YYYY-MM-DD HH:mm:ss',
        },
    ],
}