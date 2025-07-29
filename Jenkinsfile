pipeline {
    agent any

    environment {
        DOCKER_HOST = 'unix:///var/run/docker.sock'
    }

    stages {
        stage('Clone Repository') {
            steps {
                echo "📦 Clonage du projet depuis GitHub..."
                git(
                    url: 'https://github.com/Nour-Ghribi/projet-jenkins-flask.git',
                    branch: 'main',
                    credentialsId: 'github-tokenn'
                )
            }
        }

        stage('Build Docker Images') {
            steps {
                echo "🏗️ Construction des images avec docker-compose..."
                sh 'docker-compose build || exit 1'
            }
        }

        stage('Deploy to Production') {
            steps {
                echo "🚀 Déploiement des conteneurs..."
                sh 'docker-compose down --remove-orphans || true'
                sh 'docker-compose up -d || exit 1'
            }
        }

        stage('Verify Deployment') {
            steps {
                echo "✅ Vérification du déploiement..."
                sh 'docker ps || exit 1'
            }
        }
    }

    post {
        success {
            echo '✅ Déploiement réussi ! Accès : http://34.34.143.152:5000'
        }
        failure {
            echo '❌ Échec du déploiement. Vérifie les logs Jenkins.'
        }
    }
}

