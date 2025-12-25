#!/bin/bash

APP_NAME="app.py"
APP_DIR="/root/image_web"
APP_PATH="$APP_DIR/$APP_NAME"
PID_FILE="$APP_DIR/py_app.pid"
LOG_FILE="$APP_DIR/py_app.log"

start_app() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️ 程序已运行, PID: $PID"
            return
        fi
    fi

    echo "🚀 正在启动 Python 程序..."

    cd "$APP_DIR"

    # 所有输出都写入日志文件
    nohup python3 "$APP_PATH" \
        >> "$LOG_FILE" \
        2>&1 &

    echo $! > "$PID_FILE"
    echo "✅ 启动成功，PID: $(cat $PID_FILE)"
}

stop_app() {
    if [ ! -f "$PID_FILE" ]; then
        echo "⚠️ 无 PID 文件，程序可能未启动"
        return
    fi

    PID=$(cat "$PID_FILE")

    if ! ps -p $PID > /dev/null 2>&1; then
        echo "⚠️ 程序未运行"
        rm -f "$PID_FILE"
        return
    fi

    echo "🛑 正在停止 PID: $PID"
    kill "$PID"
    sleep 1

    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️ 需要强制 kill -9"
        kill -9 "$PID"
    fi

    rm -f "$PID_FILE"
    echo "✅ 已停止"
}

status_app() {
    if [ ! -f "$PID_FILE" ]; then
        echo "🔸 未运行"
        return
    fi

    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "🟢 正在运行，PID: $PID"
    else
        echo "🔸 PID 文件存在但程序未运行"
    fi
}

logs_app() {
    echo "📜 实时日志（Ctrl+C退出）："
    tail -f "$LOG_FILE"
}

case "$1" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        stop_app
        start_app
        ;;
    status)
        status_app
        ;;
    logs)
        logs_app
        ;;
    *)
        echo "用法: ./run_py.sh {start|stop|restart|status|logs}"
        ;;
esac

