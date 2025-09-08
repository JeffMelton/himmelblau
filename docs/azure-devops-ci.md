# Azure DevOps CI: VM Provisioning Smoke Test

This repository includes an on‑demand Azure Pipelines workflow that provisions a short‑lived Ubuntu 24.04 VM, validates basic connectivity using `az vm run-command`, and always tears down the resource group to avoid resource leaks.

File: `azure-pipelines.yml`

## What It Does
- Creates a unique resource group and Ubuntu 24.04 LTS VM (`Standard_B2s`) in `southcentralus` by default.
- Does not create a public IP. The pipeline uses `az vm run-command` to execute a basic sanity script on the VM (no inbound ports).
- Always deletes the resource group in a final step (`condition: always()`).

## Why On‑Demand
- The pipeline is configured with `trigger: none` and `pr: none` and is intended to be run manually while we iterate.
- After we validate infrastructure, we’ll extend the pipeline with build/install steps and Entra ID join/validation.

## Prerequisites
1. Azure DevOps project with a working Azure Resource Manager service connection (Scoped to a subscription/resource group where you can create ephemeral resources).
2. Permissions for the service connection to:
   - Create/delete resource groups
   - Create/delete compute/network resources (VM, NIC, VNet/subnet if needed, public IP is currently disabled)
3. Azure CLI is provided by the `AzureCLI@2` task in the pipeline agent. No local setup needed.

## Configure the Pipeline
1. In Azure DevOps, create/choose an Azure Resource Manager service connection.
2. Edit `azure-pipelines.yml` and set:
   - `variables.azureServiceConnection`: your service connection name
   - Optional: `location`, `vmSize`, `adminUsername`
3. Commit and push to your fork (this repo is public, so the VM can `git clone` later when we add that step).

## Running the Pipeline
1. In Azure DevOps Pipelines, select this pipeline and choose “Run pipeline”.
2. The job will:
   - Create the resource group and VM
   - Run a basic script on the VM (`echo VM OK && uname -a`)
   - Always delete the resource group

Expected duration: ~7–15 minutes (mostly VM create + delete).

## Triggering via Azure CLI (az)

You can create and/or trigger the pipeline from the Azure DevOps CLI (az + azure-devops extension).

Prerequisite: ensure the Azure DevOps CLI extension is installed and defaults are set.

```bash
# Install the Azure DevOps extension if needed
az extension add --name azure-devops

# Configure defaults (replace with your org and project)
az devops configure --defaults \
  organization=https://dev.azure.com/<ORG> \
  project=<PROJECT>
```

Create the pipeline (one-time) from this repo and YAML:

```bash
# If the pipeline doesn’t exist yet, create it once.
# Replace placeholders and adjust repository/branch as needed.
az pipelines create \
  --name "himmelblau-vm-smoke" \
  --repository https://github.com/<YOUR_GITHUB_ACCOUNT>/himmelblau-mine \
  --branch main \
  --yaml-path azure-pipelines.yml \
  --repository-type github
```

Run the pipeline on demand:

```bash
# Run by pipeline name (optionally set a branch)
az pipelines run --name "himmelblau-vm-smoke" --branch main

# Or run by pipeline ID
PIPE_ID=$(az pipelines list --query "[?name=='himmelblau-vm-smoke'].id | [0]" -o tsv)
az pipelines run --id "$PIPE_ID" --branch main
```

Pass/override variables at queue time (e.g., service connection or location):

```bash
az pipelines run \
  --name "himmelblau-vm-smoke" \
  --branch main \
  --variables azureServiceConnection="My-Service-Connection" location="southcentralus"
```

Monitor and manage runs:

```bash
# List recent runs
az pipelines runs list -o table

# Show a specific run
az pipelines runs show --id <RUN_ID>

# Cancel a running build
az pipelines runs cancel --id <RUN_ID>
```

## Variables and Defaults
- `azureServiceConnection`: REQUIRED – name of the Azure RM service connection.
- `location`: default `southcentralus`.
- `vmSize`: default `Standard_B2s`.
- `resourceGroupName` / `vmName`: include `$(Build.BuildId)` for uniqueness per run.
- `vmImageUrn`: Canonical Ubuntu 24.04 LTS Gen2 latest.

## Cost Considerations
- A small VM (`Standard_B2s`) plus managed disk + networking used only for minutes costs cents per run.
- Because deletion is synchronous, the resource group should be fully removed at the end of the job.

## Troubleshooting
- If provision fails:
  - Inspect the AzureCLI task logs for `az` command errors.
  - Check quota/permissions in the target subscription/region.
  - Ensure the service connection has Contributor permissions for the scope (or custom role with equivalent actions).
- If teardown fails:
  - The job still attempts deletion in `condition: always()`.
  - Re-run a manual cleanup: `az group delete --name <rg> --yes` (use tags `pipeline`, `runId` from the pipeline for discovery).

## Next Steps (Planned)
- VM pulls this public repo and builds from source using `make`.
- `sudo make install` to install Himmelblau packages.
- Configure Entra ID join, validate login/auth, then unjoin.
- Maintain on‑demand trigger; optionally add a scheduled/nightly integration run later.
