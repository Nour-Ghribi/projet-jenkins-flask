pipeline {
    agent any

    stages {
        stage('Cloner le projet') {
            steps {
                git 'https://github.com/Nour-Ghribi/projet-jenkins-flask.git'
            }
        }

        stage('Construire avec Docker Compose') {
            steps {
                sh 'docker-compose build'
            }
        }

        stage('Tester') {
            steps {
                sh 'docker-compose run --rm flaskapp pytest'
            }
        }

        stage('Déployer') {
            steps {
                sh 'docker-compose up -d'
            }
        }
    }
}
