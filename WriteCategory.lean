structure Category where
  Obj : Type
  Hom : Obj → Obj → Type
  id : (A : Obj) → Hom A A
  comp : (A B C : Obj) → Hom A B → Hom B C → Hom A C
  id_comp : (A B : Obj) → (f : Hom A B) → comp A A B (id A) f = f
  comp_id : (A B : Obj) → (f : Hom A B) → comp A B B f (id B) = f
  comp_assoc : (A B C D : Obj) → (f : Hom A B) → (g : Hom B C) → (h : Hom C D) →
    comp A C D (comp A B C f g) h = comp A B D f (comp B C D g h)

inductive WritingStage : Type
  | material | outline | firstDraft | finalDraft
  deriving DecidableEq

open WritingStage

inductive WritingEdge : WritingStage → WritingStage → Type
  | organize : WritingEdge material outline
  | draftFromMaterial : WritingEdge material firstDraft
  | publishFromMaterial : WritingEdge material finalDraft
  | writeFromOutline : WritingEdge outline firstDraft
  | polishFromOutline : WritingEdge outline finalDraft
  | finalize : WritingEdge firstDraft finalDraft
  | review : WritingEdge firstDraft firstDraft
  | reflect : WritingEdge firstDraft firstDraft
  | rewrite : WritingEdge firstDraft firstDraft

open WritingEdge

inductive Path : WritingStage → WritingStage → Type
  | nil : Path A A
  | cons : WritingEdge A B → Path B C → Path A C

namespace Path

def concat : Path A B → Path B C → Path A C
  | nil, q => q
  | cons e p, q => cons e (concat p q)

end Path

open Path

def writingCategory : Category :=
  { Obj := WritingStage
    Hom := Path
    id := λ _ => nil
    comp := λ _ _ _ f g => concat f g
    id_comp := λ _ _ f => by
      induction f with
      | nil => rfl
      | cons _ _ => rfl
    comp_id := λ _ _ f => by
      induction f with
      | nil => rfl
      | cons e p ih => simp [concat, ih]
    comp_assoc := λ _ _ _ _ f g h => by
      induction f with
      | nil => rfl
      | cons e p ih => simp [concat, ih]
  }
