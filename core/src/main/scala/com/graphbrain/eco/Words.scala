package com.graphbrain.eco

class Words(val words: Array[Word]=Array[Word]()) {
  def text = words.map(_.word).reduceLeft(_ + " " + _)

  def count = words.size

  override def toString =
    if (words.length > 0) words.map(_.toString).reduceLeft(_ + " " + _) else ""
}

object Words {
  def empty = new Words()
}
