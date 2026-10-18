# Sintetiza una lista de frases a WAV con las voces de Windows, sin conexión.
# Uso: powershell -NoProfile -ExecutionPolicy Bypass -File tools/tts_sapi.ps1 -JobFile <ruta.json> [-FemaleVoice "Microsoft Sabina"] [-MaleVoice "Microsoft Raul"]
# El JSON es una lista de objetos {"file": "...", "text": "...", "ssml": "...", "voice": "female|male"}.
# Motor principal: Windows.Media.SpeechSynthesis (WinRT), que expone las voces OneCore
# (Sabina femenina y Raul masculino en es-MX). Si WinRT no está disponible, se usa System.Speech (SAPI5),
# que en este equipo solo ofrece la voz femenina "Microsoft Sabina Desktop".
param(
    [Parameter(Mandatory = $true)][string]$JobFile,
    [string]$FemaleVoice = "Microsoft Sabina",
    [string]$MaleVoice = "Microsoft Raul"
)

$jobs = Get-Content -Raw -Encoding UTF8 $JobFile | ConvertFrom-Json
$useWinRT = $true
try {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media, ContentType = WindowsRuntime] | Out-Null
    [Windows.Storage.Streams.DataReader, Windows.Storage.Streams, ContentType = WindowsRuntime] | Out-Null
} catch {
    $useWinRT = $false
    Write-Output "AVISO: WinRT no disponible ($($_.Exception.Message)); se usa SAPI5 con una sola voz."
}

if ($useWinRT) {
    $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
    function Await($WinRtTask, $ResultType) {
        $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
        $netTask = $asTask.Invoke($null, @($WinRtTask))
        $netTask.Wait(-1) | Out-Null
        $netTask.Result
    }
    $all = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices
    $female = $all | Where-Object { $_.DisplayName -eq $FemaleVoice } | Select-Object -First 1
    $male = $all | Where-Object { $_.DisplayName -eq $MaleVoice } | Select-Object -First 1
    if (-not $female) { $female = $all | Where-Object { $_.Language -like 'es*' -and $_.Gender -eq 'Female' } | Select-Object -First 1 }
    if (-not $male) { $male = $all | Where-Object { $_.Language -like 'es*' -and $_.Gender -eq 'Male' } | Select-Object -First 1 }
    if (-not $male) { Write-Output "AVISO: no hay voz masculina en español; se usa la femenina para todos."; $male = $female }
    $synth = New-Object Windows.Media.SpeechSynthesis.SpeechSynthesizer
    $count = 0
    foreach ($job in $jobs) {
        $synth.Voice = if ($job.voice -eq 'male') { $male } else { $female }
        $stream = $null
        try {
            if ($job.ssml) { $stream = Await ($synth.SynthesizeSsmlToStreamAsync($job.ssml)) ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream]) }
        } catch {
            Write-Output "AVISO: fallo SSML en $($job.file); se usa texto plano. $($_.Exception.Message)"
        }
        if (-not $stream) { $stream = Await ($synth.SynthesizeTextToStreamAsync($job.text)) ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream]) }
        $size = [uint32]$stream.Size
        $reader = New-Object Windows.Storage.Streams.DataReader($stream.GetInputStreamAt(0))
        Await ($reader.LoadAsync($size)) ([uint32]) | Out-Null
        $bytes = New-Object byte[] $size
        $reader.ReadBytes($bytes)
        [IO.File]::WriteAllBytes($job.file, $bytes)
        $reader.Dispose(); $stream.Dispose()
        $count++
    }
    $synth.Dispose()
    Write-Output "Generados $count archivos con WinRT. Voz femenina: $($female.DisplayName); voz masculina: $($male.DisplayName)"
    exit 0
}

Add-Type -AssemblyName System.Speech
$sapi = New-Object System.Speech.Synthesis.SpeechSynthesizer
try { $sapi.SelectVoice("Microsoft Sabina Desktop") } catch { Write-Output "AVISO: voz SAPI5 predeterminada." }
$sapi.Rate = -1
$format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(22050, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
$count = 0
foreach ($job in $jobs) {
    $sapi.SetOutputToWaveFile($job.file, $format)
    try { if ($job.ssml) { $sapi.SpeakSsml($job.ssml) } else { $sapi.Speak($job.text) } } catch { $sapi.Speak($job.text) }
    $sapi.SetOutputToNull()
    $count++
}
$sapi.Dispose()
Write-Output "Generados $count archivos con SAPI5 (una sola voz)."
