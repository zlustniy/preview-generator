import java.time.LocalDate
import java.time.format.DateTimeFormatter

pipeline {
    agent none
    options {
        buildDiscarder(logRotator(numToKeepStr: '7', artifactNumToKeepStr: '7'))
    }

    environment {
        NAMESPACE_TEST = "itf-services-test"
        NAMESPACE_PROD = "itf-services-prod"
        DOCKER_CRED = "docker-registry-deploy_srv-credentials-id"
        DOCKER_IMAGE = "preview-generator"
    }
    stages {

        stage('Build') {
            when {
                branch 'master'
            }
            agent {
                docker {
                    image 'dc2.srvhub.tools/tools/compose'
                }
            }
            steps {
                script {
                    // Прерывание билда, если запущен новый.
                    def buildNumber = env.BUILD_NUMBER as int
                    if (buildNumber > 1) milestone(buildNumber - 1)
                    milestone(buildNumber)
                    //сборка
                    docker.withRegistry('https://dc2.srvhub.tools', DOCKER_CRED) {
                        django_image = "dc2.srvhub.tools/tmp/${DOCKER_IMAGE}_${getBranch()}"

                        sh "docker build -t ${django_image} \
                        --build-arg commit=${GIT_COMMIT} \
                        --build-arg build_datetime=${java.time.LocalDateTime.now()} \
                        -f ./Dockerfile ."

                        sh "docker tag ${django_image} ${django_image}:${buildNumber}"
                        sh "docker push ${django_image}:${buildNumber}"
                        sh "docker push ${django_image}"
                    }
                }
            }
        }

        stage('Deploy test') {
            when {
                branch 'master'
            }
            agent {
                docker {
                    image 'dc2.srvhub.tools/tools/k8s:1.18.2'
                }
            }
            steps {
                script {
                    deploy('test', NAMESPACE_TEST, "tmp/${DOCKER_IMAGE}_${getBranch()}")
                }
            }
        }

        stage('Deploy prod') {
            when {
                beforeInput true
                branch 'master'
            }
            input {
                message "Deploy to production?"
                id "simple-input"
            }
            agent {
                docker {
                    image 'dc2.srvhub.tools/tools/k8s:1.18.2'
                }
            }
            steps {
                script {
                    sshagent(credentials: ['bitbucket']) {
                        sh "git tag ${getTag()}"
                        sh "git push origin ${getTag()}"
                    }
                    deploy('prod', NAMESPACE_PROD, "${DOCKER_PROJECT}/${DOCKER_IMAGE}")
                }
            }
        }
    }
}

private void deploy(String environment, String namespace, String dockerImage) {
    docker.withRegistry('https://dc2.srvhub.tools', DOCKER_CRED) {
        sh "docker pull dc2.srvhub.tools/tmp/${DOCKER_IMAGE}_${getBranch()}"
        sh "docker tag dc2.srvhub.tools/tmp/${DOCKER_IMAGE}_${getBranch()} dc2.srvhub.tools/${dockerImage}:${env.BUILD_NUMBER}"
        sh "docker push dc2.srvhub.tools/${dockerImage}:${env.BUILD_NUMBER}"

    }
    sh "kubectl config use-context ${getContext(environment)}"
    helmRelease = "${DOCKER_IMAGE}-${environment}"
    sh "helm upgrade --install ${helmRelease} -n ${namespace} ./helm \
                                -f ./helm/values-${environment}.yaml  \
                                --set image.repository=${dockerImage} \
                                --set image.tag=${env.BUILD_NUMBER} \
                                --set version=${env.BUILD_NUMBER}"

    sh "helm test ${helmRelease} -n ${namespace}"
}

private groovy.lang.GString getContext(String env) {
    ['test': 'k8s.test', 'prod': 'k8s.prod'].get(env)
}

private getBranch() {
    env.BRANCH_NAME.replaceAll("[^a-zA-Z0-9-]", "-").toLowerCase()
}

private getTag(){
    "v"+ LocalDate.now().format(DateTimeFormatter.ofPattern("ddMMyyyy"))+"-"+env.BUILD_NUMBER;
}