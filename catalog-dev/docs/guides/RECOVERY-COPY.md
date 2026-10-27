# Copy the VM recovery directory to Windows

The copy is not needed for ERPNext to continue running. It preserves the actual
backup independently of the VM and is useful before restore/upgrade experiments.
A snapshot retained with the VM is not an independent copy of that backup.

These commands apply to the tested catalog-rehearsal-01 operation only:
`df5db457a573425d87d54b9ab037026d`. If a different plan was installed, use its ID.
Do not rerun the backup stage just to make a copy.

SSH must be enabled on the disposable test VM with an account allowed to use
sudo. The test VM address is 172.22.237.80 and the account is truenas_admin.
If SSH reports Permission denied (publickey), check Allow Password Authentication
and Password Login Groups in System > Services > SSH configuration. Keep root
login unchanged. Enter account passwords only in your own terminal.

1. In Windows PowerShell, connect using your own SSH account:

```powershell
ssh truenas_admin@172.22.237.80
```

2. In that SSH session (TrueNAS host, not an app container), create a private
   archive. This leaves the original recovery directory untouched:

```bash
sudo sh -c 'umask 077; set -C; tar -C /mnt/labpool/erpnext-catalog-test/sites/.catalog-recovery -czf - df5db457a573425d87d54b9ab037026d > /tmp/erpnext-recovery.tar.gz'
sudo chown "$(id -u):$(id -g)" /tmp/erpnext-recovery.tar.gz
sha256sum /tmp/erpnext-recovery.tar.gz
exit
```

Record the SHA256. If any command fails, stop and preserve its error; do not
broaden permissions on the source directory. If the archive already exists, the
noclobber setting deliberately stops creation; use the existing file or a new name.
Run commands individually and stop if any fails; do not copy a partial archive.

3. Back in Windows PowerShell, download and hash it:

```powershell
scp truenas_admin@172.22.237.80:/tmp/erpnext-recovery.tar.gz "$env:USERPROFILE\Downloads\erpnext-recovery.tar.gz"
Get-FileHash "$env:USERPROFILE\Downloads\erpnext-recovery.tar.gz" -Algorithm SHA256
```

Confirm the Windows hash matches the VM hash. Keep the archive in private backup
storage outside Git. It includes database contents and credential/encryption
configuration; do not upload it to a PR or paste its contents into chat.

If SSH is unavailable, use an existing private SMB share on the test VM or a
VMware transfer method instead. Do not expose the recovery directory publicly or
change production shares merely to transfer this lab backup.
