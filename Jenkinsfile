pipeline {
    agent any

    environment {
        REGISTRY = 'ghcr.io/maryamafzal123'
        TAG = "jenkins-${env.BUILD_NUMBER}"
    }

    stages {
        stage('Build backend image') {
            steps {
                sh 'docker build -t $REGISTRY/brandbazar-backend:$TAG .'
            }
        }

        stage('Checkout frontend') {
            steps {
                dir('frontend-src') {
                    git branch: 'main',
                        credentialsId: 'bitbucket-credentials',
                        url: 'https://bitbucket.org/maryamafzal123/multibrandfashionecommerce-frontend.git'
                }
            }
        }

        stage('Build frontend image') {
            steps {
                sh 'docker build --build-arg NEXT_PUBLIC_API_URL=https://aws.brandbazarbymirsa.com -t $REGISTRY/brandbazar-frontend:$TAG frontend-src'
            }
        }

        stage('Push to GHCR') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'ghcr-credentials',
                                                  usernameVariable: 'GH_USER',
                                                  passwordVariable: 'GH_TOKEN')]) {
                    sh '''
                        echo "$GH_TOKEN" | docker login ghcr.io -u "$GH_USER" --password-stdin
                        docker push $REGISTRY/brandbazar-backend:$TAG
                        docker push $REGISTRY/brandbazar-frontend:$TAG
                    '''
                }
            }
        }
    }
}