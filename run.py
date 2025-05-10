from app import create_app

app = create_app()

if __name__ == '__main__':
    # 确保在生产环境中关闭 debug 模式
    # 可以通过 app.run(host='0.0.0.0', port=5000) 使其在网络上可访问
    # 对于开发，可以使用 debug=True
    app.run(debug=True, host='0.0.0.0', port=8085)
