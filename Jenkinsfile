pipeline {
    agent any
    stages {
        stage("Preparation") {
            steps {
                echo "Working directory"
                sh "pwd"

                echo "Directory content"
                sh "ls -a -l"
            }
        }
        stage("Dependency") {
            steps {
                echo "Setup venv"
                sh "python3.8 -m venv venv"

                echo "Install dependency"
                sh "venv/bin/pip3.8 install -r requirements.txt"
            }
        }
        stage("Execute") {
            steps {
                echo "Run main"
                sh "venv/bin/python3.8 main.py"
            }
        }
    }
    post {
        success {
            echo "Success"
        }
        failure {
            echo "Failure"
        }
    }
}
