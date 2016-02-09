(ns graphbrain.web.handlers.intersect
  (:require [graphbrain.hg.ops :as hgops]
            [graphbrain.hg.id :as id]
            [graphbrain.hg.queries :as q]
            [graphbrain.web.common :as common]
            [graphbrain.web.visualvert :as vv]
            [graphbrain.web.cssandjs :as css+js]
            [graphbrain.web.views.intersect :as i]
            [graphbrain.web.encoder :as enc]
            [clojure.math.combinatorics :as combo]))

(defn- edge->links
  [edge]
  #_(combo/combinations
   (map id/eid->id
        (maps/participant-ids edge)) 2))

(defn- inters-data
  [ids user ctxt ctxts]
  #_(let [edges (q/intersect common/gbdb ids ctxts)
        verts (into #{}
               (flatten
                (map maps/participant-ids edges)))
        verts (map #(vv/id->visual common/gbdb % ctxt ctxts) verts)
        links (mapcat identity
                      (map edge->links edges))]
    {:vertices verts
     :links links
     :seeds (map id/local->global ids)
     :context (contexts/context-data
               (first ids)
               (:id user))}))

(defn- data->str
  [data]
  (clojure.string/replace (pr-str data)
                          "'" ""))

(defn- js
  [ids user ctxt ctxts]
  (str "var ptype='intersect';"
       "var data='" (enc/encode
                     (inters-data ids user ctxt ctxts))
       "';"))

(defn handle
  [request]
  #_(let
      [ids (vals (:query-params request))
       user (common/get-user request)
       ctxt (id/context (first ids))
       ctxts (contexts/active-ctxts ctxt user)]
    (common/log request (str "intersect: " ids
                             "; ctxt: " ctxt))
    (i/intersect :title "intersect"
                 :css-and-js (css+js/css+js)
                 :user user
                 :ctxt (contexts/context-data
                        (first ids)
                        (:id user))
                 :js (js ids user ctxt ctxts))))
