# Using OpenCode on Windows via WSL2 (with R and RStudio Server)

This guide is for setting up OpenCode on Windows systems. [The OSX (Mac) and Linux/Unix/etc. guide is here](https://github.com/NIEHS/ToxPipe/blob/Deployment/docs/opencode-readme.md).

> **Scope:** Windows users only. Commands are written for Debian or Ubuntu 22.04 (Jammy) inside WSL2.
> The R and RStudio Server sections are specific to R users — skip them if you only need OpenCode.

---

## Step 1: Fix WSL2 Installation on Managed or Corporate Windows Machines

The standard `wsl --install` command can fail on some Windows machines (particularly
managed/corporate laptops) with the following error:

```
wsl --install
Installing: Windows Subsystem for Linux
A specified logon session does not exist. It may already have been terminated.
```

**The cause:** Windows was unable to access a required logon session during installation,
typically because the user profile information had not yet been fully created.

**The fix** (workaround from [microsoft/WSL#9521](https://github.com/microsoft/WSL/issues/9521)):

1. Log in to your computer using an **administrative account**.
2. Log back out and log back in using your **regular, unprivileged user account**.

   This allows Windows to create the missing profile information that the installer requires.

3. You can now run the following commands successfully as your regular user  (Although in the github link, zeekus suggested to installwith admin elevation but I think it is not needed):

```powershell
wsl --install
wsl --set-default-version 2
wsl --update
wsl --list --online
```

> **Note:** `wsl --list --online` shows all available distributions.
> Ubuntu is also a common choice and the commands below are compatible with both.

After installation completes, restart your machine if prompted, then open your WSL2 terminal
from the Start menu.

---

## Step 2: Install OpenCode in WSL2

Open your WSL2 terminal and run the OpenCode install script:

```bash
curl -fsSL https://opencode.ai/install | bash
```

Then configure OpenCode to use ToxPipe models by following [`docs/opencode-readme.md`](./opencode-readme.md).

---

## Step 3: (R users) Install R and RStudio Server in WSL2

> This section is only needed if you work in R.

These instructions are based on the official Posit support article with updated content:
[Using RStudio Server in Windows WSL2](https://support.posit.co/hc/en-us/articles/360049776974-Using-RStudio-Server-in-Windows-WSL2).

```bash
# Refresh the local package index and upgrade installed system packages.
sudo apt update && sudo apt upgrade -y

# Install R, recommended R packages, R development headers, gdebi for local .deb installation,
# compiler/build tools, and common development libraries used by many R packages.
sudo apt install -y \
  r-base \
  r-base-core \
  r-recommended \
  r-base-dev \
  gdebi-core \
  build-essential \
  libcurl4-openssl-dev \
  libssl-dev \
  libxml2-dev \
  libfontconfig1-dev \
  libfreetype6-dev \
  libharfbuzz-dev \
  libfribidi-dev \
  libpng-dev \
  libtiff5-dev \
  libjpeg-dev \
  libuv1-dev \
  pkg-config

# Download the RStudio Server installer for Ubuntu 22.04 Jammy.
wget https://s3.amazonaws.com/rstudio-ide-build/server/jammy/amd64/rstudio-server-2026.01.2-418-amd64.deb

# Install RStudio Server and automatically resolve package dependencies.
sudo gdebi -n rstudio-server-2026.01.2-418-amd64.deb
```

> **Note:** The URL above is a pre-release build that has been verified to work. If you prefer
> the current stable release, visit the [RStudio Server download page](https://posit.co/download/rstudio-server/)
> and substitute the URL and filename for Ubuntu 22 (Jammy).

```bash
# Start the RStudio Server service.
sudo rstudio-server start

# Check the RStudio Server service status.
sudo rstudio-server status
```

> **Note:** WSL2 does not persist background services between sessions. If you close and
> reopen WSL2, you must run `sudo rstudio-server start` again to bring RStudio Server back up.

Open RStudio Server in your Windows browser:

```
http://localhost:8787/
```

Log in with your WSL2 Linux username and password.

> Port 8787 does not conflict with any ToxPipe service.

---

## OpenCode alongside RStudio Server: Current Limitations

OpenCode runs in any WSL2 terminal, including the **built-in terminal inside RStudio Server**
(Tools → Terminal → New Terminal). From there it can read and edit your `.R`, `.Rmd`, and `.qmd`
files, run `Rscript`, generate code, and fix bugs.

**What OpenCode cannot do:** it has no access to your live R session — loaded data frames,
the environment pane, plots, or console output. RStudio Server is a browser-based IDE and
shares no state with OpenCode.


---

## Looking Ahead: Positron

[Positron](https://positron.posit.co/) is the next-generation data science IDE from Posit
(the makers of RStudio), built for both R and Python. It is the direction to watch for a
fully integrated R + AI coding experience:

- **Positron Assistant** (currently in preview) already has context access to your loaded
  data, plots, and console history — directly addressing the limitation described above.
- OpenCode runs in Positron's integrated terminal today, with no extra configuration.
- Posit is actively deepening AI integrations; Claude Code is already supported.

As this ecosystem matures, the gap between an AI coding agent and a live R session will
likely close inside Positron.
