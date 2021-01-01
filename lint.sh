#!/usr/bin/env sh

all() { pylint; flake8; }
pylint() { python3 -m pylint --rcfile=./.pylintrc ./sys_line; }
flake8() { python3 -m flake8 ./sys_line; }

main()
{
    if (($# == 0)); then
        all
    else
        while (($# > 0)); do
            case "$1" in
                "pylint") pylint ;;
                "flake8") flake8 ;;
            esac
            shift
        done
    fi
}

main "$@"
