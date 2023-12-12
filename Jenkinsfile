pipeline {
    agent any
    
    environment {
        GIT_CREDENTIALS = "Github"
    }
    
    stages{
        
        stage('Clone Repo') {
            steps {
                git branch: 'main', credentialsId: env.GIT_CREDENTIALS, url: 'https://github.com/TobyJWalker/HOSP-Proxy.git'
            }
        }
        
        stage('Docker Stop') {
            steps {
                sh '''
                    docker stop $(docker ps -a -q)
                '''
            }
        }
        
        stage('Docker Build') {
            steps {
                sh '''
                    docker build -t proxy .
                '''
            }
        }
        
        stage('Docker Run') {
            steps {
                sh '''
                    docker run -d -p 80:5001 proxy
                '''
            }
        }
        
    }
}