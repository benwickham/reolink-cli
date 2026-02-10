#compdef reolink

# Zsh completion for reolink-cli
# Install: copy to a directory in your $fpath, or source directly

_reolink() {
    local -a commands
    commands=(
        'info:Show device information'
        'battery:Show battery status'
        'storage:Show storage information'
        'network:Show network information'
        'time:System time'
        'capabilities:Show camera capabilities'
        'motion:Motion detection'
        'ai:AI detection'
        'ir:Infrared lights'
        'spotlight:White LED spotlight'
        'status-led:Power/status LED'
        'image:Image settings'
        'encoding:Video encoding settings'
        'audio:Audio settings'
        'snap:Capture a JPEG snapshot'
        'stream:Get stream URL'
        'recordings:Recording management'
        'watch:Watch for live events'
        'siren:Siren / audio alarm'
        'push:Push notifications'
        'ftp:FTP upload'
        'email:Email alerts'
        'recording:Recording toggle'
        'reboot:Reboot the camera'
        'firmware:Firmware management'
        'ntp:NTP time sync'
        'users:User management'
    )

    _arguments -C \
        '--host[Camera IP or hostname]:host:' \
        '--user[Username]:user:' \
        '--password[Password]:password:' \
        '--channel[Channel index]:channel:' \
        '--timeout[Timeout in seconds]:timeout:' \
        '--json[Output as JSON]' \
        '--quiet[Suppress output]' \
        '--version[Show version]' \
        '--help[Show help]' \
        '1:command:->command' \
        '*::arg:->args'

    case "$state" in
        command)
            _describe 'command' commands
            ;;
        args)
            case "${words[1]}" in
                motion)
                    _values 'subcommand' 'status' 'enable' 'disable' 'sensitivity'
                    ;;
                ai)
                    _values 'subcommand' 'status' 'enable' 'disable'
                    ;;
                ir)
                    _values 'subcommand' 'status' 'set'
                    ;;
                spotlight)
                    _values 'subcommand' 'status' 'set' 'on' 'off'
                    ;;
                status-led)
                    _values 'subcommand' 'on' 'off'
                    ;;
                image|encoding|audio)
                    _values 'subcommand' 'status' 'set'
                    ;;
                recordings)
                    _values 'subcommand' 'list' 'download' 'status'
                    ;;
                siren)
                    _values 'subcommand' 'trigger' 'stop'
                    ;;
                push)
                    _values 'subcommand' 'status' 'enable' 'disable'
                    ;;
                ftp)
                    _values 'subcommand' 'status' 'enable' 'disable' 'test'
                    ;;
                email)
                    _values 'subcommand' 'status' 'enable' 'disable' 'test'
                    ;;
                recording)
                    _values 'subcommand' 'enable' 'disable'
                    ;;
                firmware)
                    _values 'subcommand' 'info' 'check' 'update'
                    ;;
                ntp)
                    _values 'subcommand' 'status' 'set'
                    ;;
                users)
                    _values 'subcommand' 'list' 'add' 'delete'
                    ;;
            esac
            ;;
    esac
}

_reolink "$@"
