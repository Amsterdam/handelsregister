#!groovy

def tryStep(String message, Closure block, Closure tearDown = null) {
    try {
        block();
    }
    catch (Throwable t) {
        slackSend message: "${env.JOB_NAME}: ${message} failure ${env.BUILD_URL}", channel: '#ci-channel', color: 'danger'

        throw t;
    }
    finally {
        if (tearDown) {
            tearDown();
        }
    }
}


node {

    stage("Checkout") {
        checkout scm
    }

    stage('Test') {
        tryStep "Test", {
            sh "docker-compose -p handelsregister -f .jenkins/docker-compose.yml build"
            sh "docker-compose -p handelsregister -f .jenkins/docker-compose.yml run -u root --rm tests"
        }, {
            sh "docker-compose -p handelsregister -f .jenkins/docker-compose.yml down"
        }
    }

    stage("Build develop image") {
        tryStep "build", {
            def image = docker.build("build.datapunt.amsterdam.nl:5000/datapunt/handelsregister:${env.BUILD_NUMBER}", "web")
            image.push()
            image.push("acceptance")
        }
    }
}

String BRANCH = "${env.BRANCH_NAME}"

if (BRANCH == "master") {

node {
    stage("Deploy to ACC") {
        tryStep "deployment", {
            build job: 'Subtask_Openstack_Playbook',
                    parameters: [
                            [$class: 'StringParameterValue', name: 'INVENTORY', value: 'acceptance'],
                            [$class: 'StringParameterValue', name: 'PLAYBOOK', value: 'deploy-handelsregister.yml'],
                            [$class: 'StringParameterValue', name: 'BRANCH', value: 'master'],
                    ]
        }
    }
}


stage('Waiting for approval') {
    slackSend channel: '#ci-channel', color: 'warning', message: 'Handelsregister is waiting for Production Release - please confirm'
    input "Deploy to Production?"
}



node {
    stage('Push production image') {
        tryStep "image tagging", {
            def image = docker.image("build.datapunt.amsterdam.nl:5000/datapunt/handelsregister:${env.BUILD_NUMBER}")
            image.pull()

            image.push("production")
            image.push("latest")
        }
    }
}

node {
    stage("Deploy") {
        tryStep "deployment", {
            build job: 'Subtask_Openstack_Playbook',
                    parameters: [
                            [$class: 'StringParameterValue', name: 'INVENTORY', value: 'production'],
                            [$class: 'StringParameterValue', name: 'PLAYBOOK', value: 'deploy-handelsregister.yml'],
                            [$class: 'StringParameterValue', name: 'BRANCH', value: 'master'],
                    ]
        }
    }
}
}