pipeline {
    agent any

    environment {
        IMAGE_BACKEND  = "smart-job-tracker-backend"
        IMAGE_FRONTEND = "smart-job-tracker-frontend"
        REGISTRY       = credentials('docker-registry-url')   // configure in Jenkins credentials
        DOCKERHUB_CRED = credentials('dockerhub-credentials') // configure in Jenkins credentials
    }

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

        stage('Backend: Install & Lint') {
            steps {
                dir('backend') {
                    sh '''
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        pip install flake8
                        flake8 app --max-line-length=110 --exit-zero
                    '''
                }
            }
        }

        stage('Backend: Run Tests (pytest)') {
            steps {
                dir('backend') {
                    sh '''
                        . venv/bin/activate
                        pytest --cov=app --cov-report=xml --junitxml=test-results.xml
                    '''
                }
            }
            post {
                always {
                    junit 'backend/test-results.xml'
                }
            }
        }

        stage('Build Docker Images') {
            steps {
                script {
                    sh "docker build -t ${IMAGE_BACKEND}:${BUILD_NUMBER} ./backend"
                    sh "docker build -t ${IMAGE_FRONTEND}:${BUILD_NUMBER} ./frontend"
                    sh "docker tag ${IMAGE_BACKEND}:${BUILD_NUMBER} ${IMAGE_BACKEND}:latest"
                    sh "docker tag ${IMAGE_FRONTEND}:${BUILD_NUMBER} ${IMAGE_FRONTEND}:latest"
                }
            }
        }

        stage('Push Images') {
            when { branch 'main' }
            steps {
                sh '''
                    echo "$DOCKERHUB_CRED_PSW" | docker login -u "$DOCKERHUB_CRED_USR" --password-stdin
                    docker tag smart-job-tracker-backend:latest $DOCKERHUB_CRED_USR/smart-job-tracker-backend:latest
                    docker tag smart-job-tracker-frontend:latest $DOCKERHUB_CRED_USR/smart-job-tracker-frontend:latest
                    docker push $DOCKERHUB_CRED_USR/smart-job-tracker-backend:latest
                    docker push $DOCKERHUB_CRED_USR/smart-job-tracker-frontend:latest
                '''
            }
        }

        stage('Deploy') {
            when { branch 'main' }
            steps {
                sh '''
                    docker compose -f docker-compose.yml pull backend frontend
                    docker compose -f docker-compose.yml up -d --no-deps backend frontend
                '''
            }
        }
    }

    post {
        success {
            echo "Build #${BUILD_NUMBER} succeeded — tests passed, images built and deployed."
        }
        failure {
            echo "Build #${BUILD_NUMBER} failed — check the stage logs above."
        }
        always {
            sh 'docker system prune -f || true'
        }
    }
}
