from app import create_app

if __name__ == '__main__':
    app = create_app()
    
    print("Запуск Genetic Mutation Analyzer...")
    print("API доступно по адресу: http://localhost:5000")
    print("Документация API: http://localhost:5000/api/")
    print("Проверка здоровья: http://localhost:5000/health")
    print("-" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )