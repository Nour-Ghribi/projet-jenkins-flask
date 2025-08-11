pipeline {
    agent any

    environment {
        DOCKER_HOST = 'unix:///var/run/docker.sock'
        GIT_REPO = 'https://github.com/Nour-Ghribi/projet-jenkins-flask.git'
        GIT_BRANCH = 'main'
        GIT_CREDENTIALS = 'github-tokenn'
    }

    stages {
        stage(' Clone Repository') {
            steps {
                echo "Clonage du projet depuis GitHub..."
                git(
                    url: "${GIT_REPO}",
                    branch: "${GIT_BRANCH}",
                    credentialsId: "${GIT_CREDENTIALS}"
                )
            }
        }

        stage(' Run Unit Tests') {
            steps {
                echo "Lancement des tests unitaires..."
                // Important : l’activation de l’environnement virtuel doit être dans la même ligne de commande (sh)
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate && \
                    pip install --upgrade pip && \
                    pip install -r requirements.txt && \
                    pip install pytest && \
                    pytest --maxfail=1 --disable-warnings -q
                '''
            }
        }

        stage('🏗 Build Docker Images') {
            steps {
                echo "Construction des images Docker..."
                sh 'docker-compose build'
            }
        }

        stage(' Deploy to Production') {
            steps {
                script {
                    echo "Déploiement des conteneurs..."
                    try {
                        sh 'docker-compose down --remove-orphans || true'
                        sh 'docker-compose up -d'
                    } catch (err) {
                        echo "⚠️ Échec du déploiement, rollback..."
                        sh 'docker-compose down || true'
                        sh 'docker-compose up -d'
                        error("Rollback effectué, déploiement initial échoué.")
                    }
                }
            }
        }

        stage('🔍 Verify Deployment') {
            steps {
                echo "Vérification des conteneurs en cours..."
                sh 'docker ps'
                echo "Application disponible sur : http://34.34.160.216:5000"
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline terminé avec succès !'
        }
        failure {
            echo '❌ Le pipeline a échoué. Vérifiez les logs Jenkins.'
        }
    }
}
