# coding: utf8


from keras.layers import Conv1D as _Conv1D
from keras.layers import Dense as _Dense
from keras.layers import Embedding as _Embedding
from keras.layers import LSTM, Dropout, Flatten, Input, MaxPool1D, Reshape
from keras.models import Model
from keras.utils import plot_model

from autogoal.contrib.keras import KerasNeuralNetwork
from autogoal.grammar import (
    Block,
    Boolean,
    Categorical,
    CfgInitializer,
    Discrete,
    Graph,
    GraphGrammar,
    Path,
    generate_cfg,
)


class Reshape2D(Reshape):
    def __init__(self):
        super(Reshape2D, self).__init__(target_shape=(-1, 1))


class Embedding(_Embedding):
    def __init__(self, output_dim: Discrete(32, 128)):
        super(Embedding, self).__init__(input_dim=1000, output_dim=output_dim)


class Dense(_Dense):
    def __init__(self, units: Discrete(128, 1024), **kwargs):
        super(Dense, self).__init__(units=units, **kwargs)


class Conv1D(_Conv1D):
    def __init__(self, filters: Discrete(5, 20), kernel_size: Categorical(3, 5, 7)):
        super(Conv1D, self).__init__(
            filters=filters, kernel_size=kernel_size, padding="causal"
        )


def build_grammar():
    grammar = GraphGrammar(
        start=Path(
            "PreprocessingModule",
            "ReductionModule",
            "FeaturesModule",
            "ClassificationModule",
        ),
        initializer=CfgInitializer(),
    )

    # productions for Preprocessing
    grammar.add("PreprocessingModule", Embedding)
    grammar.add("PreprocessingModule", Path(Dense, Reshape2D))
    # grammar.add("PreprocessingModule", Path(Embedding, LSTM))
    # TODO: Bert

    # productions for Reduction
    grammar.add("ReductionModule", "ConvModule")
    grammar.add("ReductionModule", "DenseModule")
    grammar.add("ConvModule", Path(Conv1D, MaxPool1D, "ConvModule"))
    grammar.add("ConvModule", Path(Conv1D, MaxPool1D))
    # grammar.add("ReductionModule", Path(Conv2D, MaxPool2D, "DenseModule"))

    # productions for Features
    grammar.add("FeaturesModule", Path(Flatten, "DenseModule"))
    # TODO: Attention

    # productions for Classification
    grammar.add("ClassificationModule", Path("DenseModule", "Final"))
    grammar.add("Final", Dense, kwargs=dict(units=4, activation="softmax"))

    # productions to expand Dense layers
    grammar.add("DenseModule", Path(Dense, "DenseModule"))
    grammar.add("DenseModule", Block(Dense, "DenseModule"))
    grammar.add("DenseModule", Dense)

    return grammar


class Classifier(KerasNeuralNetwork):
    def __init__(self):
        super(Classifier, self).__init__(
            grammar=build_grammar(),
            input_shape=(1000,),
            optimizer="rmsprop",
            loss="categorical_crossentropy",
        )


class Tokenizer:
    def __init__(self, stopwords: Boolean(), stemming: Boolean()):
        self.stopwords = stopwords
        self.stemming = stemming


class Pipeline:
    def __init__(self, tokenizer: Tokenizer, classifier: Classifier):
        self.tokenizer = tokenizer
        self.classifier = classifier


def main():
    grammar = generate_cfg(Pipeline)
    print(grammar)

    pipeline: Pipeline = grammar.sample()
    pipeline.classifier.model.summary()

if __name__ == "__main__":
    main()