pipeline {
    agent any

    environment {
        // Variables d'environnement
        PROJECT_DIR = "/home/jenkins/workspace/flask-docker-deploy"
    }

    stages {
        // ÉTAPE 1 : CLONER LE PROJET DEPUIS GITHUB
        stage('Clone Repository') {
            steps {
                echo "📦 Clonage depuis GitHub..."
                git branch: 'main',
                     url: 'https://github.com/Nour-Ghribi/projet-jenkins-flask.git '
            }
        }

        // ÉTAPE 2 : INSTALLER DOCKER ET DOCKER COMPOSE (SI BESOIN)
        stage('Install Docker') {
            steps {
                echo "🔧 Vérification / installation de Docker..."
                sh 'which docker || (sudo apt update && sudo apt install -y docker.io)'
                sh 'which docker-compose || sudo apt install -y docker-compose'
            }
        }

        // ÉTAPE 3 : CONSTRUIRE LES IMAGES DOCKER
        stage('Build Docker Images') {
            steps {
                echo "🏗️ Construction des images Docker..."
                sh 'docker-compose build'
            }
        }

        // ÉTAPE 4 : DÉPLOYER SUR LA VM GCP
        stage('Deploy to GCP VM') {
            steps {
                echo "🚀 Déploiement sur la VM GCP"
                sshagent(['gcp-vm-ssh-credentials-id']) {
                    sh '''
                        echo "🛑 Arrêt des conteneurs existants..."
                        docker-compose down

                        echo "🔄 Mise à jour du projet..."
                        git pull origin main

                        echo "🏗️ Reconstruire les images Docker..."
                        docker-compose build

                        echo "✅ Lancement des conteneurs..."
                        docker-compose up -d
                    '''
                }
            }
        }

        

        // ÉTAPE 6 : SUCCÈS DU DÉPLOIEMENT
        stage('Deployment Success') {
            steps {
                echo "✅ Le déploiement sur GCP est terminé !"
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline Jenkins réussi !"
        }
        failure {
            echo "❌ Échec du pipeline Jenkins. Vérifie les logs."
        }
    }
}