pipeline {
    agent any
    environment {
        /* Git username */
        gitUsername = ""
        /* Automation repository name */
        repositoryName = ""
        /* Custom image name */
        imageName = ""
        /* Custom image tag/version */
        imageTag = ""
        /* Custom container name */
        containerName = ""
    }
    stages {
        stage("Preparation") {
            steps {
                echo "Working directory"
                sh "pwd"
                echo "Cloning the project"
                sh "git clone git@github.com:${gitUsername}/${repositoryName}.git"
                echo "Viewing images"
                sh "docker images"
                echo "Viewing containers"
                sh "docker ps -a"
                echo "Building the image"
                sh """cd ${repositoryName}/
                    docker build -t ${imageName}:${imageTag} .
                """
            }
        }
        stage("Run Tests") {
            steps {
                echo "Running the container"
                sh "docker run -i --name=${containerName} ${imageName}:${imageTag}"
            }
        }
        stage("Post-processing") {
            steps {
                echo "Saving the report"
                sh "docker cp ${containerName}:/code/report ./${repositoryName}/report"
                echo "Saving the log"
                sh "docker cp ${containerName}:/code/log ./${repositoryName}/log"
                echo "Removing the container"
                sh "docker rm ${containerName}"
                echo "Removing the image"
                sh "docker rmi ${imageName}:${imageTag}"
            }
        }
    }
    post {
        success {
            echo "Viewing images"
            sh "docker images"
            echo "Viewing containers"
            sh "docker ps -a"
            echo "Execution successful"
        }
        failure {
            echo "Viewing images"
            sh "docker images"
            echo "Viewing containers"
            sh "docker ps -a"
            echo "Execution failed"
        }
    }
}