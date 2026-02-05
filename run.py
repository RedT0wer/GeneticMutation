from app import create_app

if __name__ == '__main__':
    app = create_app()
    
    # pyinstaller --onefile --add-data "app;app" --add-data "config.py;." run.py
    print("Запуск Genetic Mutation Analyzer...")
    print("Сайт доступно по адресу: http://localhost:5000")
    print("-" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )