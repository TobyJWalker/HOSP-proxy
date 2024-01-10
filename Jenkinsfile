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
        
        stage('Docker Run') {
            steps {
                sh '''
                    docker-compose up --force-recreate --build -d
                    docker image prune -f
                '''
            }
        }
        
    }
}