# Azure DevOps CI: VM Provisioning Smoke Test

This repository includes an on‑demand, fully CLI-parameterized Azure Pipelines workflow. It provisions a short‑lived Ubuntu 24.04 VM, validates basic connectivity with `az vm run-command`, builds and installs Himmelblau from source, seeds Entra ID configuration for Himmelblau on the VM, and always tears down the resource group.

File: `azure-pipelines.yml`

## Refactored: Pure CLI Parameterization
- **All configurable options are pipeline parameters.**
- No need to predefine or authorize variables in the web UI; set parameters at queue time via CLI or UI.
- Works out-of-the-box for old-school, TTY-native workflows.

## What It Does
- Creates a unique resource group and Ubuntu 24.04 LTS VM (`Standard_B2s`) in `southcentralus` (customizable).
- No public IP; uses `az vm run-command` (secure, inbound-port-free provisioning).
- Always deletes the resource group (job runs `condition: always()`).
- Optionally builds/installs Himmelblau (`enableBuildInstall` parameter).
- Optionally seeds `/etc/himmelblau/himmelblau.conf` and configures Entra unless parameter omitted.

## Pipeline Parameters (all CLI-settable!)
- `azureServiceConnection` (*string*, REQUIRED) – name of ARM service connection.
- `location` (*string*, default `southcentralus`)
- `vmSize` (*string*, default `Standard_B2s`)
- `adminUsername` (*string*, default `azureuser`)
- `enableBuildInstall` (*boolean*, default `false`)
- `enableEntraSetup` (*boolean*, default `false`)
- `repoUrl` (*string*, default: pipeline repo)
- `repoBranch` (*string*, default: pipeline branch)
- `entraPrimaryDomain` (*string*, default: `melton.cloud`)
- `entraAuthorityHost` (*string*, default: `login.microsoftonline.com`)
- `aadPamAllowGroups` (*string*, optional)

## Example: CLI-Driven Pipeline Run

Infra only (all defaults):
```bash
az pipelines run --name "himmelblau-vm-smoke"
```

Build+install (with branch override):
```bash
az pipelines run \
  --name "himmelblau-vm-smoke" \
  --parameters enableBuildInstall=true repoBranch=your-feature-branch
```

All options, all CLI (entirely TTY-native):
```bash
az pipelines run \
  --name "himmelblau-vm-smoke" \
  --parameters azureServiceConnection=sc-himmelblau-testing-arm enableBuildInstall=true enableEntraSetup=true location=westeurope entraPrimaryDomain=contoso.com repoUrl=https://github.com/contoso/himmelblau.git repoBranch=feature/test-infra
```
- No web UI variables needed, ever.
- All toggles are visible and queue-time flexible.

## Migrating From UI Variables
You may **safely delete all pipeline variables from the Azure DevOps web UI** for this pipeline. Only the parameters defined at the top of `azure-pipelines.yml` are respected.

## Pipeline Setup and Triggering
- See original content for initial pipeline creation, service connection setup, and troubleshooting resource group/VM issues.
- Always pass parameters using `--parameters ...` for queue-time driven runs.

## Troubleshooting
- If you see "Cannot set variable at queue time":
    - This means the variable is still defined in the UI, or you are using an old YAML. Use only parameters, not `variables:` for queue-time CLI workflows!
- If a resource is not provisioned or destroyed, check the AzureCLI@2 step logs in the build for details.

## TTY-First Policy
This pipeline is now optimized for operations folks and heavy CLI users. You never have to switch to the browser to tweak variables ever again.