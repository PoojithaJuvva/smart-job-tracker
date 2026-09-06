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

        stage('Stop Old Containers') {
            steps {
                bat 'docker compose down || exit 0'
            }
        }

        stage('Build Docker Images') {
            steps {
                bat 'docker compose build'
            }
        }

        stage('Run Containers') {
            steps {
                bat 'docker compose up -d'
            }
        }
    }

    post {
        success {
            echo "Build #${BUILD_NUMBER} succeeded — tests passed, containers rebuilt and running."
        }
        failure {
            echo "Build #${BUILD_NUMBER} failed — check the stage logs above."
        }
    }
}