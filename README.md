# Application Manager
This is a college and job application manager run by a rest API containerized by Docker and Kubernetes. It is configured to run in the Google cloud and utilizes other cloud softwares such as Google storage buckets to maintain a collection of images attached to the applications. The multiple endpoints are described below. 


## Endpoints
#### /help [GET]
Provides general information about the project including a couple sample calls
#### /help/college [GET]
Provides specific information about using the college geared endpoints
#### /help/job [GET]
Provides specific information about using the job geared endpoints
#### /add/college [POST]
This request contains a json object formatted to the parameters and fields provided in **/help/college**. It will first validate the json object to ensure the worker is able to process the request. It will then use the rabbitMQ channel to send the request body to the worker node. The worker node will add a row into the 'college' table in the database and write any pictures to the Google storage bucket. The end point will return the primary key of the database row for future reference. 
#### /add/job [POST]
This request contains a json object formatted to the parameters and fields provided in **/help/job**. It will first validate the json object to ensure the worker is able to process the request. It will then use the rabbitMQ channel to send the request body to the worker node. The worker node will add a row into the 'job' table in the database and write any pictures to the Google storage bucket. The end point will return the primary key of the database row for future reference. 
#### /query/college/[field]/[value]/[Optional inequality] [GET]
This request queries all college applications looking at the specified field and value. It has an optional inequality parameter that can be used to describe the relationship between field and value. A sample query could look like **/query/collge/GPA/3.0/geq** where this means you will be returned all the applications that have a GPA greater than or equal to 3.0. **The default is equal**. The possible optional parameters are: lt, leq, eq, ne, gt, geq.
#### /query/job/[field]/[value]/[Optional inequality] [GET]
This request queries all college applications looking at the specified field and value. It has an optional inequality parameter that can be used to describe the relationship between field and value. A sample query could look like **/query/collge/required_pay/15/leq** where this means you will be returned all the applications that have a required pay less than or equal to $15/hour. **The default is equal**. The possible optional parameters are: lt, leq, eq, ne, gt, geq.
#### /update/college/[field]/[value] [PUT]
This request updates the given field to the given value using the primary key of the application you wish to update which is given in the request body in JSON format. 
#### /update/job/[field]/[value] [PUT]
This request updates the given field to the given value using the primary key of the application you wish to update which is given in the request body in JSON format. 
#### /delete/college [DELETE]
This request deletes a row based on the primary key of the application which is given in the request body in JSON format.
#### /delete/job [DELETE]
This request deletes a row based on the primary key of the application which is given in the request body in JSON format.
