(ns graphbrain.web.handlers.input
  (:require [graphbrain.web.common :as common]
            [graphbrain.web.contexts :as contexts]
            [graphbrain.db.gbdb :as gb]
            [graphbrain.db.id :as id]
            [graphbrain.db.maps :as maps]
            [graphbrain.db.urlnode :as url]
            [graphbrain.disambig.edgeguesser :as edg]
            [graphbrain.braingenerators.pagereader :as pr]
            [graphbrain.eco.eco :as eco]
            [graphbrain.eco.parsers.chat :as chat]
            [graphbrain.string :as gbstr]
            [graphbrain.db.entity :as entity]
            [graphbrain.db.searchinterface :as si]))

(defn- input-reply-fact
  [root-id vertex]
  (let [goto-id (if (maps/edge? vertex)
                  (id/eid->id (second (maps/ids vertex)))
                  root-id)]
    (pr-str {:type :fact
             :newedges (list (:id vertex))
             :gotoid goto-id})))

(defn- input-reply-url
  [root-id]
  (pr-str {:type :url
           :gotoid root-id}))

(defn- input-reply-search
  [count results]
  (pr-str {:type :search
           :count count
           :results results}))

(defn- sentence-type
  [sentence]
  (if (and (gbstr/no-spaces? sentence)
           (or (.startsWith sentence "http://") (.startsWith sentence "https://")))
    :url :fact))

(defn- process-fact
  [user root sentence ctxts]
  (let
      [env {:root (maps/vertex->eid root) :user (:id user)}
       res (first (eco/parse-str chat/chat sentence env))]
    (if (id/edge? res)
      (let [edge-id (edg/guess common/gbdb res sentence ctxts)
            edge (maps/id->vertex edge-id)
            edge (assoc edge :score 1)]
        (gb/putv! common/gbdb edge (:id user))
        (input-reply-fact (:id root) edge)))))

(defn process-search
  [user root q ctxts]
  (let [results (si/query common/gbdb q ctxts)
        results-list (map #(list (id/eid->id %) (entity/description %)) results)]
    (if (empty? results-list)
      (process-fact user root q ctxts)
      (input-reply-search (count results-list) results-list))))

(defn process-url
  [user root sentence ctxts]
  (let [url-id (url/url->id sentence)]
    (pr/extract-knowledge! common/gbdb sentence ctxts (:id user))
    (input-reply-url url-id)))

(defn handle
  [request]
  (let [sentence ((request :form-params) "sentence")
        root-id ((request :form-params) "root")
        user (common/get-user request)
        root (if root-id (gb/getv common/gbdb root-id
                                  (contexts/active-ctxts request user)))
        ctxts (contexts/active-ctxts request user)]
    (case (sentence-type sentence)
      :fact (process-search user root sentence ctxts)
      :url (process-url user root sentence ctxts))))