pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "flask-app"
        DOCKER_TAG = "latest"
    }

    stages {
        stage('Clone repository') {
            steps {
                git 'https://github.com/Nour-Ghribi/projet-jenkins-flask.git'
            }
        }

        stage('Build Docker image') {
            steps {
                script {
                    sh 'docker build -t $DOCKER_IMAGE:$DOCKER_TAG .'
                }
            }
        }

        stage('Run Docker container') {
            steps {
                script {
                    // Stop previous container if running
                    sh 'docker rm -f flask-container || true'

                    // Run new container
                    sh 'docker run -d -p 5000:5000 --name flask-container $DOCKER_IMAGE:$DOCKER_TAG'
                }
            }
        }
    }
}

