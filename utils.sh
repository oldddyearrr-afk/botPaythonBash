#!/bin/bash
# utils.sh - دوال مساعدة للنظام

# دالة لتنظيف الملفات المؤقتة
cleanup_temp_files() {
    local TEMP_DIR="${1:-/tmp}"
    local PATTERN="${2:-smart_clip_*.mp4}"
    
    local DELETED_COUNT=0
    
    for file in "$TEMP_DIR"/$PATTERN; do
        if [[ -f "$file" ]]; then
            rm -f "$file" 2>/dev/null && ((DELETED_COUNT++))
        fi
    done
    
    echo "{\"status\": \"success\", \"deleted_files\": $DELETED_COUNT}"
    return 0
}

# دالة للتحقق من توفر FFmpeg
check_ffmpeg() {
    if command -v ffmpeg &>/dev/null; then
        local VERSION=$(ffmpeg -version 2>/dev/null | head -n1)
        echo "{\"status\": \"success\", \"installed\": true, \"version\": \"$VERSION\"}"
        return 0
    else
        echo "{\"status\": \"failed\", \"installed\": false, \"error\": \"FFmpeg not found\"}"
        return 1
    fi
}

# دالة للتحقق من مساحة القرص المتاحة
check_disk_space() {
    local PATH_TO_CHECK="${1:-.}"
    
    # الحصول على المساحة المتاحة بالميجابايت
    local AVAILABLE_MB=$(df -m "$PATH_TO_CHECK" | awk 'NR==2 {print $4}')
    
    echo "{\"status\": \"success\", \"available_mb\": $AVAILABLE_MB}"
    return 0
}

# دالة لإنشاء مجلد آمن
create_safe_directory() {
    local DIR_PATH="$1"
    
    if [[ -z "$DIR_PATH" ]]; then
        echo "{\"status\": \"failed\", \"error\": \"Directory path required\"}"
        return 1
    fi
    
    mkdir -p "$DIR_PATH" 2>/dev/null
    
    if [[ -d "$DIR_PATH" ]]; then
        echo "{\"status\": \"success\", \"path\": \"$DIR_PATH\"}"
        return 0
    else
        echo "{\"status\": \"failed\", \"error\": \"Failed to create directory\"}"
        return 1
    fi
}

# دالة لتسجيل رسالة في ملف log
log_message() {
    local LOG_FILE="${1:-logs/bash.log}"
    local MESSAGE="$2"
    local LEVEL="${3:-INFO}"
    
    local TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[$TIMESTAMP] [$LEVEL] $MESSAGE" >> "$LOG_FILE"
    
    echo "{\"status\": \"success\", \"logged\": true}"
    return 0
}

# تنفيذ الدالة المطلوبة
case "${1:-}" in
    cleanup)
        cleanup_temp_files "$2" "$3"
        ;;
    check_ffmpeg)
        check_ffmpeg
        ;;
    check_disk)
        check_disk_space "$2"
        ;;
    create_dir)
        create_safe_directory "$2"
        ;;
    log)
        log_message "$2" "$3" "$4"
        ;;
    *)
        echo "{\"status\": \"failed\", \"error\": \"Unknown command\"}"
        exit 1
        ;;
esac
