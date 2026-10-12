$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$versao = 'v1.0.0'
$base = "https://huggingface.co/rhasspy/piper-voices/resolve/$versao/pt/pt_BR/cadu/medium"
$modelo = Join-Path $PSScriptRoot 'pt_BR-cadu-medium.onnx'
$config = "$modelo.json"
$modeloTemporario = "$modelo.download"
$configTemporaria = "$config.download"
$sha256Esperado = '765f0809a6ea9035d4a6d0d008dbf8876e68b2dd32029312672fa8f405bdb535'
$modeloExiste = Test-Path -LiteralPath $modelo
$configExiste = Test-Path -LiteralPath $config

if ($modeloExiste -ne $configExiste) {
    throw 'Há apenas um dos arquivos da voz. Restaure o par completo antes de continuar.'
}

if (-not $modeloExiste) {
    if (-not (Test-Path -LiteralPath $modeloTemporario)) {
        Invoke-WebRequest -Uri "$base/pt_BR-cadu-medium.onnx" -OutFile $modeloTemporario
    }
    $sha256Obtido = (Get-FileHash -LiteralPath $modeloTemporario -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($sha256Obtido -ne $sha256Esperado) {
        throw "A verificação do modelo falhou. SHA-256 recebido: $sha256Obtido"
    }

    if (-not (Test-Path -LiteralPath $configTemporaria)) {
        Invoke-WebRequest -Uri "$base/pt_BR-cadu-medium.onnx.json" -OutFile $configTemporaria
    }
    $dadosConfig = Get-Content -LiteralPath $configTemporaria -Encoding UTF8 -Raw | ConvertFrom-Json
    if ($dadosConfig.language.code -ne 'pt_BR' -or $dadosConfig.dataset -ne 'cadu') {
        throw 'O arquivo de configuração baixado não corresponde à voz Cadu em português brasileiro.'
    }

    Move-Item -LiteralPath $modeloTemporario -Destination $modelo
    Move-Item -LiteralPath $configTemporaria -Destination $config
} else {
    $sha256Obtido = (Get-FileHash -LiteralPath $modelo -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($sha256Obtido -ne $sha256Esperado) {
        throw "A voz Cadu existente não passou na verificação. SHA-256: $sha256Obtido"
    }
    $dadosConfig = Get-Content -LiteralPath $config -Encoding UTF8 -Raw | ConvertFrom-Json
    if ($dadosConfig.language.code -ne 'pt_BR' -or $dadosConfig.dataset -ne 'cadu') {
        throw 'A configuração existente não corresponde à voz Cadu em português brasileiro.'
    }
}

$python = (Resolve-Path (Join-Path $PSScriptRoot '..\..\.venv\Scripts\python.exe')).Path
& $python -m pip install piper-tts==1.8.0
if ($LASTEXITCODE -ne 0) {
    throw 'A instalação do Piper falhou. Os arquivos da voz foram baixados e verificados.'
}

Write-Output 'Voz Cadu e Piper instalados. Reinicie o JARVIS para usar a nova voz.'
