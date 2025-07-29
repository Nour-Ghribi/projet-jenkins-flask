pipeline {
    agent any

    stages {
        stage('Clone Repository') {
            steps {
                echo "📦 Clonage du projet depuis GitHub..."
                git(
                    url: 'https://github.com/Nour-Ghribi/projet-jenkins-flask.git',
                    branch: 'main',  // ou 'master' si tu utilises cette branche
                    changelog: true,
                    poll: true
                )
            }
        }

        stage('Build Docker Images') {
            steps {
                echo "🏗️ Construction des images avec docker-compose..."
                sh 'docker-compose build'
            }
        }

        stage('Deploy to Production') {
            steps {
                echo "🚀 Déploiement des conteneurs..."
                sh 'docker-compose down --remove-orphans || true'
                sh 'docker-compose up -d'
            }
        }

        stage('Verify Deployment') {
            steps {
                echo "✅ Vérification du déploiement..."
                sh 'docker ps'
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

