$ErrorActionPreference = 'Stop'
$utf8 = New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null

function Wait-WinRtResult($operation, [Type] $resultType) {
    $method = [System.WindowsRuntimeSystemExtensions].GetMethods() |
        Where-Object {
            $_.Name -eq 'AsTask' -and
            $_.IsGenericMethodDefinition -and
            $_.GetParameters().Count -eq 1 -and
            $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
        } |
        Select-Object -First 1

    if ($null -eq $method) {
        throw 'Não foi possível preparar a síntese de voz do Windows.'
    }

    $task = $method.MakeGenericMethod($resultType).Invoke($null, @($operation))
    $task.Wait()
    return $task.Result
}

try {
    $synth = [Activator]::CreateInstance(
        [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows, ContentType=WindowsRuntime]
    )

    $vozes = [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows, ContentType=WindowsRuntime]::AllVoices
    $voz = $vozes |
        Where-Object { $_.Language -eq 'pt-BR' -and $_.Gender.ToString() -eq 'Male' -and $_.DisplayName -match 'Daniel' } |
        Select-Object -First 1

    if ($null -eq $voz) {
        $voz = $vozes |
            Where-Object { $_.Language -eq 'pt-BR' -and $_.Gender.ToString() -eq 'Male' } |
            Select-Object -First 1
    }

    if ($null -ne $voz) {
        $synth.Voice = $voz
    }

    [Console]::Out.WriteLine('READY')
    [Console]::Out.Flush()
}
catch {
    [Console]::Out.WriteLine("INIT_ERROR:$($_.Exception.Message)")
    [Console]::Out.Flush()
    exit 1
}

while ($null -ne ($linha = [Console]::In.ReadLine())) {
    $stream = $null
    $audio = $null
    $tocador = $null

    try {
        $pedido = $linha | ConvertFrom-Json
        $synth.Options.SpeakingRate = [double]$pedido.velocidade
        $synth.Options.AudioPitch = [double]$pedido.tonalidade

        $operacao = $synth.SynthesizeTextToStreamAsync([string]$pedido.texto)
        $stream = Wait-WinRtResult $operacao ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream, Windows, ContentType=WindowsRuntime])
        $audio = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($stream)
        $audio.Position = 0
        $tocador = [System.Media.SoundPlayer]::new($audio)
        $tocador.PlaySync()

        [Console]::Out.WriteLine('OK')
        [Console]::Out.Flush()
    }
    catch {
        [Console]::Out.WriteLine("ERROR:$($_.Exception.Message)")
        [Console]::Out.Flush()
    }
    finally {
        if ($null -ne $tocador) { $tocador.Dispose() }
        if ($null -ne $audio) { $audio.Dispose() }
        if ($null -ne $stream) { $stream.Dispose() }
    }
}

$synth.Dispose()
