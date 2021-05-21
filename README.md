# Serverless Selenium UI Testing

This repository contains the resources referred in [this blog post](https://aws.amazon.com/blogs/devops/serverless-ui-testing-using-selenium-aws-lambda-aws-fargate-and-aws-developer-tools/). Follow the steps below to deploy this sample application to run serverless UI testing using Selenium, AWS Lambda, AWS Fargate, and AWS Developer Tools

***

### Steps to deploy this Application

Step 1: Create an AWS CodeCommit repository following [the documentation](https://docs.aws.amazon.com/codecommit/latest/userguide/how-to-create-repository.html) and checkout the newly create repository.

Step 2: Copy the content of this GitHub repository to your newly created CodeCommit repository and run `git push` to upload the content to the remote repostiory.

Step 3: Create a CloudFormation stack using the `pipeline.yaml` template to launch the pipeline in AWS CodePipeline.

***

This package depends on and may incorporate or retrieve a number of third-party
software packages (such as open source packages) at install-time or build-time
or run-time ("External Dependencies"). The External Dependencies are subject to
license terms that you must accept in order to use this package. If you do not
accept all of the applicable license terms, you should not use this package. We
recommend that you consult your company’s open source approval policy before
proceeding.

Provided below is a list of External Dependencies and the applicable license
identification as indicated by the documentation associated with the External
Dependencies as of Amazon's most recent review.

THIS INFORMATION IS PROVIDED FOR CONVENIENCE ONLY. AMAZON DOES NOT PROMISE THAT
THE LIST OR THE APPLICABLE TERMS AND CONDITIONS ARE COMPLETE, ACCURATE, OR
UP-TO-DATE, AND AMAZON WILL HAVE NO LIABILITY FOR ANY INACCURACIES. YOU SHOULD
CONSULT THE DOWNLOAD SITES FOR THE EXTERNAL DEPENDENCIES FOR THE MOST COMPLETE
AND UP-TO-DATE LICENSING INFORMATION.

YOUR USE OF THE EXTERNAL DEPENDENCIES IS AT YOUR SOLE RISK. IN NO EVENT WILL
AMAZON BE LIABLE FOR ANY DAMAGES, INCLUDING WITHOUT LIMITATION ANY DIRECT,
INDIRECT, CONSEQUENTIAL, SPECIAL, INCIDENTAL, OR PUNITIVE DAMAGES (INCLUDING
FOR ANY LOSS OF GOODWILL, BUSINESS INTERRUPTION, LOST PROFITS OR DATA, OR
COMPUTER FAILURE OR MALFUNCTION) ARISING FROM OR RELATING TO THE EXTERNAL
DEPENDENCIES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN
IF AMAZON HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. THESE LIMITATIONS
AND DISCLAIMERS APPLY EXCEPT TO THE EXTENT PROHIBITED BY APPLICABLE LAW.

* In this solution, [FFmpeg](https://ffmpeg.org/) has been compiled only with the flag `--enable-libxcb` (check the [Dockerfile](Dockerfile) for the configuration used) hence it falls under [![License: LGPL v2.1](https://img.shields.io/badge/License-LGPLv2.1-blue)](http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)  

***

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

