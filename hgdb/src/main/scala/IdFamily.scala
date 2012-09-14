package com.graphbrain.hgdb


object IdFamily extends Enumeration {
  type IdFamily = Value
  val Global, User, UserSpace, EType, URL, UserURL, Rule, Source = Value

  def family(id: String) = {
    val parts = ID.parts(id)
    val nparts = ID.numberOfParts(id)
    if (parts(0) == "user")
      if (nparts == 1)
        Global
      else if (nparts == 2)
        User
      else if (parts(2) == "url")
        UserURL
      else
        UserSpace
    else if (parts(0) == "rtype")
      if (nparts == 1)
        Global
      else
        EType
    else if (parts(0) == "url")
      if (nparts == 1)
        Global
      else
        URL
    else if (parts(0) == "rule")
      if (nparts == 1)
        Global
      else
        Rule
    else if (parts(0) == "source")
      if (nparts == 1)
        Global
      else
        Source
    else
      Global
  }
}