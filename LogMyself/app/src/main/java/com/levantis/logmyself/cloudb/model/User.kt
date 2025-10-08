package com.levantis.logmyself.cloudb.model

data class User (
    var googleId: String,
    var name: String? = null,
    var email: String? = null
)