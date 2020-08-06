pipeline {
  agent none

  parameters {
    string(name: 'GIT_COMMIT', defaultValue: 'master', description: 'Commit SHA or origin branch to deploy')
  }

  stages {
    stage('release: dev') {
      steps {
        ci_pipeline("dev", params.GIT_COMMIT)
      }
    }


    stage('release: staging') {
      when {
          expression {
              milestone label: "release-staging"
              input message: 'Deploy to staging?'
              return true
          }
          beforeAgent true
      }

      steps {
        ci_pipeline("staging", params.GIT_COMMIT)
      }
    }


    stage('release: prod') {
      when {
          expression {
              milestone label: "release-prod"
              input message: 'Deploy to prod?'
              return true
          }
          beforeAgent true
      }

      steps {
        ci_pipeline("prod", params.GIT_COMMIT)
      }
    }
  }
}

void ci_pipeline(env, version) {
  lock("company-matching-service-ci-pipeline-${env}") {
    build job: "ci-pipeline", parameters: [
        string(name: "Team", value: "data-workspace-apps"),
        string(name: "Project", value: "company-matching-service"),
        string(name: "Environment", value: env),
        string(name: "Version", value: version)
    ]
  }
}
