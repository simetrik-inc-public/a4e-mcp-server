# CLI usage

## Running as a script

you can run the CLI commands just by typing:

```bash
python -m a4e.cli --help
```

for example, if you want to launch the dev server:

```bash
python -m a4e.cli dev start --directory file-store/agent-store
```

## Running as a python package

## troubleshooting

### if you can't launch the development server

1. verify that nothing is running in the port 5000

   windows:

   ```console
   netstat -ano | findstr :5000
   ```

   if you see a service that is currently running in that port, kill it and try to launch the dev server again

   windows:

   ```console
   taskkill /PID 12345 /T /F
   ```

2. try to launch just the dev server

   ```bash
   python a4e/dev_runner.py --agent-path file-store/agent-store/{your-agent-id}
   ```

   this command should launch an uvicorn services that runs on port 5000

3. try to manually run ngrok once the server is running
   ```bash
   ngrok http 5000
   ```
