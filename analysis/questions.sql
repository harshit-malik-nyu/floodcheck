SELECT provenance,COUNT(*) runs,AVG(n_flags) mean_flags,MIN(n_flags) min_flags,MAX(n_flags) max_flags FROM observations GROUP BY provenance ORDER BY provenance;
SELECT provenance,SUM(n_flags>0) flagged_runs,COUNT(*) runs,AVG(n_flags>0) flagged_rate FROM observations GROUP BY provenance ORDER BY provenance;
