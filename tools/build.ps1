function Get-Key-Press {
    Param(
        [int]$Timeout
    )
    while ($true) {
        if ([System.Console]::KeyAvailable -eq $true) {
            $keyObject = [System.Console]::ReadKey($true)
            break
        }
        Start-Sleep -Milliseconds $Timeout
    }
    return $keyObject
}


function Show-Main {
    Write-Host "This is a Build PS Script"
    Write-Host "Make sure to change the HOST Uri in the api.urls file before continuing"
    Write-Host "Press (Enter) Key to Continue or any other key to exit. " -NoNewline
    $inputKey = Get-Key-Press -Timeout 200
    if ($inputKey.Key -ne "Enter") {
        Write-Host "Exiting..."
        return
    }
    Write-Host "Continuing..."
}

Show-Main