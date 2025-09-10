# Azure DevOps CI: VM Provisioning Smoke Test

This repository includes an on‑demand, CLI-driven Azure Pipelines workflow. It provisions a short‑lived Ubuntu 24.04 VM, validates basic connectivity, builds and installs Himmelblau from source, and can seed Entra ID configuration—all without web UI variables or queue-time GUI toggles.

File: `azure-pipelines.yml`

## Pure CLI Parameterization
- All relevant configuration is controlled via pipeline parameters: `enableBuildInstall`, `enableEntraSetup`, and `repoBranch`.
- The repo URL is hardcoded and does not need to be set at runtime.
- No variables are required (or even recommended) in the Azure DevOps web UI.

## Pipeline Parameters (all CLI-settable)
- `enableBuildInstall` (*boolean*, default `false`)
- `enableEntraSetup` (*boolean*, default `false`)
- `repoBranch` (*string*, default: empty; falls back to current pipeline branch if blank)

Example: CLI run (default infra-only):
```bash
az pipelines run --name "himmelblau-vm-smoke"
```

Example: Enable build, specify a branch:
```bash
az pipelines run \
  --name "himmelblau-vm-smoke" \
  --parameters enableBuildInstall=true repoBranch=feature/test-fixes
```

Example: Enable Entra config as well:
```bash
az pipelines run \
  --name "himmelblau-vm-smoke" \
  --parameters enableBuildInstall=true enableEntraSetup=true repoBranch=feature/test-fixes
```

## Migrating From UI Variables
You may **delete all pipeline variables from the Azure DevOps web UI** for this pipeline. Only the parameters declared in `azure-pipelines.yml` are honored at queue time.

## Troubleshooting
- If the VM provisioning or build fails, review the AzureCLI@2 step logs in the pipeline run for specifics.
- If you see errors about queue-time variable setting, make sure you're only passing the three supported parameters as shown above.

## Summary
- All logic and options are settable from the CLI at queue time—no browser required for DevOps!
- The pipeline is now fully optimized for a TTY-native, scriptable workflow.
