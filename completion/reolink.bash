# Bash completion for reolink-cli
# Source this file or add to ~/.bashrc:
#   source /path/to/reolink.bash

_reolink_complete() {
    local cur prev commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Top-level commands
    commands="info battery storage network time capabilities motion ai ir spotlight status-led image encoding audio snap stream recordings watch siren push ftp email recording reboot firmware ntp users"

    # Global flags
    local global_flags="--host --user --password --channel --timeout --json --quiet --version --help"

    case "${prev}" in
        reolink)
            COMPREPLY=( $(compgen -W "${commands} ${global_flags}" -- "${cur}") )
            return 0
            ;;
        motion)
            COMPREPLY=( $(compgen -W "status enable disable sensitivity" -- "${cur}") )
            return 0
            ;;
        ai)
            COMPREPLY=( $(compgen -W "status enable disable" -- "${cur}") )
            return 0
            ;;
        ir)
            COMPREPLY=( $(compgen -W "status set" -- "${cur}") )
            return 0
            ;;
        spotlight)
            COMPREPLY=( $(compgen -W "status set on off" -- "${cur}") )
            return 0
            ;;
        status-led)
            COMPREPLY=( $(compgen -W "on off" -- "${cur}") )
            return 0
            ;;
        image)
            COMPREPLY=( $(compgen -W "status set" -- "${cur}") )
            return 0
            ;;
        encoding)
            COMPREPLY=( $(compgen -W "status set" -- "${cur}") )
            return 0
            ;;
        audio)
            COMPREPLY=( $(compgen -W "status set" -- "${cur}") )
            return 0
            ;;
        recordings)
            COMPREPLY=( $(compgen -W "list download status" -- "${cur}") )
            return 0
            ;;
        siren)
            COMPREPLY=( $(compgen -W "trigger stop" -- "${cur}") )
            return 0
            ;;
        push)
            COMPREPLY=( $(compgen -W "status enable disable" -- "${cur}") )
            return 0
            ;;
        ftp)
            COMPREPLY=( $(compgen -W "status enable disable test" -- "${cur}") )
            return 0
            ;;
        email)
            COMPREPLY=( $(compgen -W "status enable disable test" -- "${cur}") )
            return 0
            ;;
        recording)
            COMPREPLY=( $(compgen -W "enable disable" -- "${cur}") )
            return 0
            ;;
        firmware)
            COMPREPLY=( $(compgen -W "info check update" -- "${cur}") )
            return 0
            ;;
        ntp)
            COMPREPLY=( $(compgen -W "status set" -- "${cur}") )
            return 0
            ;;
        users)
            COMPREPLY=( $(compgen -W "list add delete" -- "${cur}") )
            return 0
            ;;
        set)
            # Context-dependent — offer common flags
            COMPREPLY=( $(compgen -W "--help" -- "${cur}") )
            return 0
            ;;
        --stream)
            COMPREPLY=( $(compgen -W "main sub" -- "${cur}") )
            return 0
            ;;
        --format)
            COMPREPLY=( $(compgen -W "rtsp rtmp" -- "${cur}") )
            return 0
            ;;
        --level)
            COMPREPLY=( $(compgen -W "admin guest" -- "${cur}") )
            return 0
            ;;
        --filter)
            COMPREPLY=( $(compgen -W "motion person vehicle animal" -- "${cur}") )
            return 0
            ;;
    esac

    # Default: offer global flags if starting with -
    if [[ "${cur}" == -* ]]; then
        COMPREPLY=( $(compgen -W "${global_flags}" -- "${cur}") )
        return 0
    fi

    COMPREPLY=( $(compgen -W "${commands}" -- "${cur}") )
    return 0
}

complete -F _reolink_complete reolink
