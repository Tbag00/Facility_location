(* Type record of a Facility Location Problem *)

type t = {
  n:  int; (* numero sedi *)
  m:  int; (* numero clienti *)
  f:  int array; (* costo apertura fabbriche *)
  dj: int array; (* domanda cliente *)
  c:  int array array; (* matrice costo stpedizione *)
  ui: int array; (* capacita fabbriche ignorato nel caso capacitated=false *)
}
