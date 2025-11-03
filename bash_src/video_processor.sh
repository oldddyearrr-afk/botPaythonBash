#!/bin/bash
# video_processor.sh - معالج الفيديو الرئيسي باستخدام FFmpeg

set -e  # إيقاف عند أي خطأ

# دالة لتسجيل مقطع فيديو مع علامة مائية
# المعاملات:
#   $1: SOURCE_URL - رابط البث المباشر
#   $2: OUTPUT_PATH - مسار حفظ الفيديو
#   $3: DURATION - مدة المقطع بالثواني
#   $4: WATERMARK_TEXT - نص العلامة المائية (اختياري)
#   $5: WATERMARK_ENABLED - تفعيل العلامة (true/false)
record_clip_with_watermark() {
    local SOURCE_URL="$1"
    local OUTPUT_PATH="$2"
    local DURATION="$3"
    local WATERMARK_TEXT="${4:-}"
    local WATERMARK_ENABLED="${5:-true}"
    
    # حذف الملف القديم إن وجد
    [[ -f "$OUTPUT_PATH" ]] && rm -f "$OUTPUT_PATH"
    
    # بناء الأمر الأساسي
    local FFMPEG_CMD=(
        ffmpeg -y
        -hide_banner -loglevel error
        -reconnect 1
        -reconnect_streamed 1
        -reconnect_delay_max 5
        -timeout 10000000
        -i "$SOURCE_URL"
        -t "$DURATION"
        -async 1
        -vsync passthrough
        -c:v libx264
        -preset veryfast
        -tune zerolatency
        -crf 24
        -g 30
        -keyint_min 30
        -sc_threshold 0
        -c:a aac
        -b:a 128k
        -ar 44100
        -ac 2
        -shortest
        -avoid_negative_ts make_zero
        -fflags "+genpts+igndts+discardcorrupt"
        -max_delay 0
        -movflags "+faststart"
    )
    
    # إضافة العلامة المائية إذا كانت مفعلة
    if [[ "$WATERMARK_ENABLED" == "true" ]] && [[ -n "$WATERMARK_TEXT" ]]; then
        # تنظيف النص من المحارف الخاصة
        local ESCAPED_TEXT=$(echo "$WATERMARK_TEXT" | sed "s/:/\\\\:/g" | sed "s/'/\\\\'/g")
        
        local WATERMARK_FILTER="drawtext=text='${ESCAPED_TEXT}':x=w-mod(100*t\\,w+tw):y=h-th-80:fontsize=32:fontcolor=white@0.95:borderw=0.8:bordercolor=black@0.6"
        
        FFMPEG_CMD+=(-vf "$WATERMARK_FILTER")
    fi
    
    # إضافة مسار الإخراج
    FFMPEG_CMD+=("$OUTPUT_PATH")
    
    # تنفيذ الأمر
    "${FFMPEG_CMD[@]}" 2>/tmp/ffmpeg_error.log
    
    # التحقق من نجاح العملية
    if [[ -f "$OUTPUT_PATH" ]]; then
        local FILE_SIZE=$(stat -f%z "$OUTPUT_PATH" 2>/dev/null || stat -c%s "$OUTPUT_PATH" 2>/dev/null)
        if [[ $FILE_SIZE -gt 5120 ]]; then
            echo '{"status": "success", "output": "'$OUTPUT_PATH'", "size": '$FILE_SIZE'}'
            return 0
        fi
    fi
    
    echo '{"status": "failed", "error": "Output file too small or missing"}'
    return 1
}

# دالة لضغط الفيديو (عملية إضافية)
compress_video() {
    local INPUT_PATH="$1"
    local OUTPUT_PATH="$2"
    local CRF="${3:-28}"  # قيمة افتراضية 28
    
    if [[ ! -f "$INPUT_PATH" ]]; then
        echo '{"status": "failed", "error": "Input file not found"}'
        return 1
    fi
    
    ffmpeg -y -hide_banner -loglevel error \
        -i "$INPUT_PATH" \
        -c:v libx264 \
        -crf "$CRF" \
        -preset faster \
        -c:a copy \
        "$OUTPUT_PATH" 2>/tmp/ffmpeg_compress_error.log
    
    if [[ -f "$OUTPUT_PATH" ]]; then
        local FILE_SIZE=$(stat -f%z "$OUTPUT_PATH" 2>/dev/null || stat -c%s "$OUTPUT_PATH" 2>/dev/null)
        echo '{"status": "success", "output": "'$OUTPUT_PATH'", "size": '$FILE_SIZE'}'
        return 0
    else
        echo '{"status": "failed", "error": "Compression failed"}'
        return 1
    fi
}

# دالة للحصول على معلومات الفيديو
get_video_info() {
    local VIDEO_PATH="$1"
    
    if [[ ! -f "$VIDEO_PATH" ]]; then
        echo '{"status": "failed", "error": "File not found"}'
        return 1
    fi
    
    local DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$VIDEO_PATH")
    local SIZE=$(stat -f%z "$VIDEO_PATH" 2>/dev/null || stat -c%s "$VIDEO_PATH" 2>/dev/null)
    
    echo "{\"status\": \"success\", \"duration\": $DURATION, \"size\": $SIZE}"
    return 0
}

# تنفيذ الدالة المطلوبة بناءً على المعاملات
case "${1:-}" in
    record)
        record_clip_with_watermark "$2" "$3" "$4" "$5" "$6"
        ;;
    compress)
        compress_video "$2" "$3" "$4"
        ;;
    info)
        get_video_info "$2"
        ;;
    *)
        echo '{"status": "failed", "error": "Unknown command. Use: record|compress|info"}'
        exit 1
        ;;
esac
