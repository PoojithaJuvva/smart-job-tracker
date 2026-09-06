pipeline {
    agent any

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                dir('backend') {
                    bat 'python -m venv venv'
                    bat 'venv\\Scripts\\python -m pip install --upgrade pip'
                    bat 'venv\\Scripts\\python -m pip install -r requirements.txt'
                }
            }
        }

        stage('Run Tests') {
            steps {
                dir('backend') {
                    bat 'venv\\Scripts\\python -m pytest --junitxml=test-results.xml'
                }
            }
            post {
                always {
                    junit 'backend/test-results.xml'
                }
            }
        }
    }

    post {
        success {
            echo "Build #${BUILD_NUMBER} succeeded — dependencies installed and all tests passed. Run 'docker compose up --build' manually to build and deploy containers."
        }
        failure {
            echo "Build #${BUILD_NUMBER} failed — check the stage logs above."
        }
    }
}