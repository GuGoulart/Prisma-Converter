$scriptsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptsDir
$ws = New-Object -ComObject WScript.Shell
$desktop = $ws.SpecialFolders('Desktop')
$shortcutPath = [System.IO.Path]::Combine($desktop, 'Prisma Converter.lnk')

if (Test-Path $shortcutPath) {
    Remove-Item $shortcutPath -Force
}

$icoPath = Join-Path $projectDir "static\logo.ico"
$vbsPath = Join-Path $scriptsDir "Iniciar_Prisma.vbs"

$s = $ws.CreateShortcut($shortcutPath)
$s.TargetPath = 'C:\Windows\System32\wscript.exe'
$s.Arguments = "`"$vbsPath`""
$s.WorkingDirectory = $projectDir
$s.IconLocation = "$icoPath,0"
$s.Description = 'Iniciar Prisma Converter em modo local'
$s.Save()

# Notifica o Windows Explorer para atualizar o cache de ícones no Desktop
try {
    $code = @"
    [System.Runtime.InteropServices.DllImport("shell32.dll")]
    public static extern void SHChangeNotify(int wEventId, int uFlags, IntPtr dwItem1, IntPtr dwItem2);
"@
    $type = Add-Type -MemberDefinition $code -Name Shell32 -Namespace Win32 -PassThru
    $type::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)
} catch {}
